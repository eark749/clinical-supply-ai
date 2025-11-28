# Clinical Supply Database Schema

## 📋 Overview
Database for managing clinical trial supply chain operations including materials, inventory, orders, shipments, and patient enrollment.

**Database Name:** `clinical-supply`  
**Total Tables:** 40  
**Port:** 5433

---

## 🔑 Core Entities & Key Relationships

### **1. MATERIALS & SPECIFICATIONS**

#### `material_master`
Master data for all clinical trial materials
- **Key Columns:** `Material Number`, `Material Description`, `Material type`, `Trial Alias`
- **Relationships:** Links to almost all other tables via `Material Number`

#### `materials`
Simplified material information
- **Key Columns:** `material_number`, `lilly_number`, `material_type`, `plant`
- **Related to:** `batch_master`, `manufacturing_orders`

#### `material_specification`
Technical specifications for materials
- **Key Columns:** `Material ID`, `Characteristic Name`, `Plant Id`, `Trial Alias`

#### `bom_details` (Bill of Materials)
Component breakdown for manufacturing
- **Key Columns:** `Material Number`, `Material Component`, `BOM Item Number`, `Plant`
- **Relationships:** Defines what components make up finished materials

---

### **2. TRIALS & STUDIES**

#### `materials_per_study`
Links materials to specific clinical trials
- **Key Columns:** `Material`, `Trial Alias`, `Country ID`, `Study Approval Status`
- **Relationships:** Connects `material_master` ↔ trials by country

---

### **3. BATCHES & LOTS**

#### `batch_master`
Manufacturing batch information
- **Key Columns:** `Batch number`, `Material`, `Plant`, `Trial Alias`, `Expiration date`
- **Related to:** All inventory and shipment tables

#### `batch_geneology`
Batch lineage and traceability
- **Key Columns:** `Batch number`, `Material`, `Order Number`, `Vendor Batch Number`
- **Relationships:** Tracks parent-child batch relationships

#### `inspection_lot`
Quality control and inspections
- **Key Columns:** `batch_number`, `inspection_lot_number`, `usage_decision_code`, `trial_alias`

---

### **4. INVENTORY MANAGEMENT**

#### `complete_warehouse_inventory`
Full warehouse stock details
- **Key Columns:** `lot_number`, `item_number`, `warehouse_id`, `trial_alias`, `expiration_date`

#### `affiliate_warehouse_inventory`
Affiliate-level inventory
- **Key Columns:** `lot_number`, `wh_id`, `package_number`, `study_code`, `expiration_date`

#### `global_gateway_inventory_report`
Global inventory summary
- **Key Columns:** `Protocol`, `Part ID`, `Lot ID (Client)`, `Quantity Available`, `Facility`

#### `available_inventory_report`
Site-level availability
- **Key Columns:** `Trial Name`, `Location`, `Lot`, `Package Type Description`, `Expiry Date`

#### `lot_status_report`
Lot expiration tracking
- **Key Columns:** `Trial Alias`, `Lot Number`, `Expiration Date`, `DNSA (Days)`

---

### **5. MANUFACTURING & ORDERS**

#### `manufacturing_orders`
Production orders
- **Key Columns:** `order_id`, `fing_batch`, `ly_number`, `fing_material`, `trial_alias`, `plant`
- **Relationships:** Links to `planned_orders`, `batch_master`, `material_master`

#### `planned_orders`
Future production planning
- **Key Columns:** `Order Number`, `Product Number`, `Trial Alias`, `Planning Version`

#### `allocated_materials_to_orders`
Material allocation tracking
- **Key Columns:** `order_id`, `fing_batch`, `material_component`, `material_component_batch`
- **Relationships:** Links orders to specific batches and materials

#### `order_phases`
Order operation tracking
- **Key Columns:** `trial_alias`, `order_num`, `operation_num`, `planned_end_date`

---

### **6. PURCHASING**

#### `purchase_requirement`
Purchase requisitions
- **Key Columns:** `Purchase Requisition Number`, `Material`, `Order Number`, `Plant`

#### `purchase_order_quantities`
PO quantities and dates
- **Key Columns:** `Purchasing document number`, `Item number of purchasing document`, `Material Group`

#### `purchase_order_kpi`
Purchase order performance metrics
- **Key Columns:** `Purchasing document number`, `Material`, `Vendor`, `Trial Alias`

---

### **7. SHIPMENTS & DISTRIBUTION**

#### `shipment_summary_report`
Shipment overview
- **Key Columns:** `Order Number`, `Trial Alias`, `Site Number`, `Lot Number`, `Tracking Number`
- **Relationships:** Links orders → sites → lots

#### `shipment_status_report`
Real-time shipment status
- **Key Columns:** `Shipment`, `LPN#`, `Order Number`, `Site`, `Warehouse`

#### `warehouse_and_site_shipment_tracking_report`
Detailed shipment tracking
- **Key Columns:** `order_number`, `trial_alias`, `tracking_number`, `wh_id`, `hu_id`
- **Relationships:** Complete shipment lifecycle tracking

#### `distribution_order_report`
Distribution orders to sites
- **Key Columns:** `trial_alias`, `site_id`, `order_number`, `ivrs_number`

#### `outstanding_site_shipment_status_report`
Pending shipments
- **Key Columns:** `Trial Alias`, `Site Number`, `Shipment (#)`, `Days Outstanding`

#### `ip_shipping_timelines_report`
Shipping time expectations
- **Key Columns:** `ip_helper`, `ip_timeline`, `country_name`

---

### **8. PATIENT & ENROLLMENT**

#### `patient_status_and_treatment_report`
Patient tracking
- **Key Columns:** `Trial Alias`, `site`, `patient`, `Visit`, `treatment`

#### `study_level_enrollment_report`
Study-level enrollment metrics
- **Key Columns:** `trial_alias`, `total_enrolled_actual`, `enrollment_rate_monthly_actual`

#### `country_level_enrollment_report`
Country-level enrollment
- **Key Columns:** `trial_alias`, `country_name`, `total_enrolled_actual`

#### `metrics_over_time_report`
Time-series enrollment data
- **Key Columns:** `study_alias`, `site_reference_number`, `patients_enrolled_actual`

#### `enrollment_rate_report`
Monthly enrollment rates
- **Key Columns:** `Trial Alias`, `Country`, `Site`, `Year`, `Months`

---

### **9. QUALITY & COMPLIANCE**

#### `re-evaluation`
Sample re-evaluation requests
- **Key Columns:** `ID`, `LY Number`, `Lot Number`, `Sample Status`, `Analytical Lab`

#### `excursion_detail_report`
Temperature/condition excursions
- **Key Columns:** `Excursion ID`, `Trial Alias`, `Shipment Number`, `Lot Number`, `LPN`

#### `qdocs`
Quality documentation
- **Key Columns:** `ly_number`, `material_name`, `status`, `approved_dates`

#### `rim`
Regulatory information management
- **Key Columns:** `clinical_study_v`, `ly_number_c`, `status_v`, `approved_date_c`

#### `nmrf` (New Material Request Form)
Material creation requests
- **Key Columns:** `Material Number`, `LY Number`, `Trial Alias`, `BOM Status`

---

### **10. PLANNING & REQUIREMENTS**

#### `material_requirements`
MRP planning data
- **Key Columns:** `Material ID`, `Plant ID`, `MRP element number`, `Trial Alias`

#### `material_country_requirements`
Country-specific material needs
- **Key Columns:** `Material Number`, `Countries`, `Trial Alias`

#### `planned_order_recipe`
Production recipe timing
- **Key Columns:** `Recipe`, `Phase`, `Recipe Days`, `STANDARD`, `DELUXE`

#### `inventory_detail_report`
Detailed inventory status
- **Key Columns:** `STUDY_ID`, `LOT_NUMBER`, `PACKAGE_NUMBER`, `PACKAGE_STATUS`

---

## 🔗 Key Relationships Map

```
Trial Alias (Study ID)
    ├── material_master
    ├── materials_per_study
    ├── batch_master
    ├── manufacturing_orders
    ├── shipment_summary_report
    └── patient_status_and_treatment_report

Material Number
    ├── material_master (master)
    ├── bom_details (components)
    ├── batch_master (batches)
    ├── manufacturing_orders
    └── purchase_requirement

Batch/Lot Number
    ├── batch_master (master)
    ├── batch_geneology (lineage)
    ├── complete_warehouse_inventory
    ├── shipment_summary_report
    └── re-evaluation

Order Number
    ├── manufacturing_orders
    ├── planned_orders
    ├── distribution_order_report
    └── shipment_summary_report

Plant ID
    ├── material_master
    ├── batch_master
    ├── manufacturing_orders
    └── warehouse locations

Site Number
    ├── distribution_order_report
    ├── shipment_summary_report
    ├── patient_status_and_treatment_report
    └── enrollment reports
```

---

## 📊 Common Identifier Columns

| Identifier | Purpose | Found In Tables |
|------------|---------|-----------------|
| `trial_alias` / `Trial Alias` | Study identifier | ~30 tables |
| `material_number` / `Material Number` | Material identifier | ~15 tables |
| `batch_number` / `lot_number` | Batch/Lot identifier | ~20 tables |
| `order_number` / `order_id` | Order identifier | ~10 tables |
| `plant` / `Plant` | Manufacturing location | ~12 tables |
| `ly_number` / `LY Number` | Lilly internal number | ~8 tables |
| `site_id` / `Site Number` | Clinical site | ~6 tables |
| `warehouse_id` / `wh_id` | Warehouse location | ~5 tables |

---

## 💡 Usage Notes

1. **Trial Alias** is the primary key linking most operational tables
2. **Material Number** connects materials → batches → inventory → shipments
3. **Lot/Batch Numbers** track material from production → warehouse → site → patient
4. **Order Numbers** link planning → manufacturing → distribution
5. All tables have an auto-generated `id` column (primary key)
6. Original "ID" columns are renamed to `original_id` to avoid conflicts

---

**Generated:** $(date)  
**Script:** `upload_csv_to_postgres.py`

