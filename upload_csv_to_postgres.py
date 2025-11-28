#!/usr/bin/env python3
"""
Script to upload CSV files from synthetic_clinical_data folder to PostgreSQL database.

Database Configuration:
- Database: clinical-supply
- Port: 5433
- Username: postgres
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import getpass
from pathlib import Path
import re
from typing import Dict, List


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'clinical-supply',
    'user': 'postgres'
}

# Directory containing CSV files
CSV_DIRECTORY = 'synthetic_clinical_data'


def sanitize_column_name(column_name: str) -> str:
    """
    Sanitize column names to be PostgreSQL-friendly.
    
    Args:
        column_name: Original column name
        
    Returns:
        Sanitized column name
    """
    # Convert to lowercase
    name = column_name.lower()
    
    # Replace spaces and special characters with underscores
    name = re.sub(r'[^\w\s]', '_', name)
    name = re.sub(r'\s+', '_', name)
    
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = 'col_' + name
    
    # Handle empty names
    if not name:
        name = 'unnamed_column'
    
    return name


def get_postgres_type(dtype) -> str:
    """
    Map pandas dtype to PostgreSQL type.
    
    Args:
        dtype: Pandas data type
        
    Returns:
        PostgreSQL type as string
    """
    dtype_str = str(dtype)
    
    if 'int' in dtype_str:
        return 'BIGINT'  # Use BIGINT instead of INTEGER to handle large numbers
    elif 'float' in dtype_str:
        return 'DOUBLE PRECISION'
    elif 'bool' in dtype_str:
        return 'BOOLEAN'
    elif 'datetime' in dtype_str:
        return 'TIMESTAMP'
    elif 'date' in dtype_str:
        return 'DATE'
    else:
        return 'TEXT'


def create_table(cursor, table_name: str, df: pd.DataFrame) -> None:
    """
    Create a PostgreSQL table based on DataFrame structure.
    
    Args:
        cursor: PostgreSQL cursor
        table_name: Name of the table to create
        df: DataFrame containing the data
    """
    # Sanitize column names
    sanitized_columns = {col: sanitize_column_name(col) for col in df.columns}
    
    # Check if 'id' column already exists after sanitization
    has_id_column = 'id' in [sanitized_col.lower() for sanitized_col in sanitized_columns.values()]
    
    # If 'id' column exists, rename it to avoid conflict with primary key
    if has_id_column:
        new_sanitized_columns = {}
        for col, sanitized_col in sanitized_columns.items():
            if sanitized_col.lower() == 'id':
                new_sanitized_columns[col] = 'original_id'
            else:
                new_sanitized_columns[col] = sanitized_col
        sanitized_columns = new_sanitized_columns
    
    # Build CREATE TABLE statement
    columns_def = []
    for col, sanitized_col in sanitized_columns.items():
        pg_type = get_postgres_type(df[col].dtype)
        columns_def.append(f'"{sanitized_col}" {pg_type}')
    
    columns_str = ',\n    '.join(columns_def)
    
    # Drop table if exists and create new one
    drop_query = f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'
    create_query = f'''
    CREATE TABLE "{table_name}" (
        id SERIAL PRIMARY KEY,
        {columns_str}
    );
    '''
    
    cursor.execute(drop_query)
    cursor.execute(create_query)
    
    print(f"  ✓ Created table: {table_name}")


def insert_data(cursor, table_name: str, df: pd.DataFrame) -> int:
    """
    Insert data from DataFrame into PostgreSQL table.
    
    Args:
        cursor: PostgreSQL cursor
        table_name: Name of the table
        df: DataFrame containing the data
        
    Returns:
        Number of rows inserted
    """
    if df.empty:
        print(f"  ⚠ No data to insert for {table_name}")
        return 0
    
    # Sanitize column names
    sanitized_columns = [sanitize_column_name(col) for col in df.columns]
    
    # Check if 'id' column exists and rename it to avoid conflict
    has_id_column = 'id' in [col.lower() for col in sanitized_columns]
    if has_id_column:
        sanitized_columns = ['original_id' if col.lower() == 'id' else col for col in sanitized_columns]
    
    # Rename DataFrame columns to match sanitized names
    df_copy = df.copy()
    df_copy.columns = sanitized_columns
    
    # Replace NaN with None for proper NULL insertion
    df_copy = df_copy.where(pd.notnull(df_copy), None)
    
    # Prepare insert query
    columns_str = ', '.join([f'"{col}"' for col in sanitized_columns])
    placeholders = ', '.join(['%s'] * len(sanitized_columns))
    insert_query = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
    
    # Insert data in batches
    batch_size = 1000
    total_rows = len(df_copy)
    
    for i in range(0, total_rows, batch_size):
        batch = df_copy.iloc[i:i+batch_size]
        data = [tuple(row) for row in batch.values]
        cursor.executemany(insert_query, data)
        
        # Progress indicator
        progress = min(i + batch_size, total_rows)
        print(f"  → Inserted {progress}/{total_rows} rows", end='\r')
    
    print(f"  ✓ Inserted {total_rows} rows into {table_name}           ")
    return total_rows


def get_table_name_from_filename(filename: str) -> str:
    """
    Convert CSV filename to table name.
    
    Args:
        filename: CSV filename
        
    Returns:
        Table name
    """
    # Remove .csv extension and use the filename as table name
    table_name = filename.replace('.csv', '')
    return table_name


def load_csv_to_postgres(csv_path: str, cursor, conn) -> Dict[str, any]:
    """
    Load a single CSV file into PostgreSQL.
    
    Args:
        csv_path: Path to CSV file
        cursor: PostgreSQL cursor
        conn: PostgreSQL connection
        
    Returns:
        Dictionary with load statistics
    """
    filename = os.path.basename(csv_path)
    table_name = get_table_name_from_filename(filename)
    
    print(f"\n📄 Processing: {filename}")
    print(f"  → Loading CSV file...")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"  ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Create table
        create_table(cursor, table_name, df)
        
        # Insert data
        rows_inserted = insert_data(cursor, table_name, df)
        
        # Commit transaction
        conn.commit()
        
        return {
            'filename': filename,
            'table_name': table_name,
            'status': 'success',
            'rows': rows_inserted,
            'columns': len(df.columns)
        }
        
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error processing {filename}: {str(e)}")
        return {
            'filename': filename,
            'table_name': table_name,
            'status': 'failed',
            'error': str(e)
        }


def main():
    """Main function to orchestrate CSV upload to PostgreSQL."""
    
    print("=" * 70)
    print("CSV to PostgreSQL Upload Script")
    print("=" * 70)
    
    # Get password
    password = getpass.getpass(f"Enter password for PostgreSQL user '{DB_CONFIG['user']}': ")
    DB_CONFIG['password'] = password
    
    # Check if CSV directory exists
    csv_dir = Path(CSV_DIRECTORY)
    if not csv_dir.exists():
        print(f"\n✗ Error: Directory '{CSV_DIRECTORY}' not found!")
        sys.exit(1)
    
    # Get list of CSV files
    csv_files = sorted(csv_dir.glob('*.csv'))
    
    if not csv_files:
        print(f"\n✗ Error: No CSV files found in '{CSV_DIRECTORY}'!")
        sys.exit(1)
    
    print(f"\n📊 Found {len(csv_files)} CSV files to process")
    
    # Connect to PostgreSQL
    try:
        print(f"\n🔌 Connecting to PostgreSQL...")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"  ✓ Connected successfully!")
        
    except psycopg2.Error as e:
        print(f"\n✗ Error connecting to PostgreSQL: {e}")
        sys.exit(1)
    
    # Process each CSV file
    results = []
    for csv_file in csv_files:
        result = load_csv_to_postgres(str(csv_file), cursor, conn)
        results.append(result)
    
    # Close connection
    cursor.close()
    conn.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    
    print(f"\n✓ Successful: {len(successful)}")
    print(f"✗ Failed: {len(failed)}")
    
    if successful:
        total_rows = sum(r['rows'] for r in successful)
        print(f"\n📊 Total rows inserted: {total_rows:,}")
        print("\nSuccessfully loaded tables:")
        for r in successful:
            print(f"  • {r['table_name']}: {r['rows']:,} rows, {r['columns']} columns")
    
    if failed:
        print("\n⚠ Failed uploads:")
        for r in failed:
            print(f"  • {r['filename']}: {r.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("✓ Upload process completed!")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

