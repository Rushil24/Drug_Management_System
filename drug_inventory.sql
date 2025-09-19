-- Roles
CREATE TABLE roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE -- e.g. 'govt', 'hospital_admin', 'vendor', 'warehouse_staff'
);

-- Users
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  role_id INT NOT NULL,
  organization_id INT, -- pointer to vendor/hospital if needed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME,
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Locations (warehouses, hospitals)
CREATE TABLE locations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  type ENUM('warehouse','hospital','govt_dept') NOT NULL,
  address TEXT,
  contact VARCHAR(100)
);

-- Vendors
CREATE TABLE vendors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  contact_person VARCHAR(255),
  contact_email VARCHAR(255),
  rating FLOAT DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Drug master
CREATE TABLE drugs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  generic_name VARCHAR(255),
  code VARCHAR(64) UNIQUE, -- internal SKU / barcode
  unit VARCHAR(50) NOT NULL, -- e.g. 'tablet', 'bottle'
  reorder_level INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Drug batches (inventory at batch/granular level)
CREATE TABLE drug_batch (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  drug_id INT NOT NULL,
  location_id INT NOT NULL,
  batch_no VARCHAR(128),
  quantity INT NOT NULL DEFAULT 0,
  unit_cost DECIMAL(10,2) DEFAULT NULL,
  manufacture_date DATE DEFAULT NULL,
  expiry_date DATE DEFAULT NULL,
  status ENUM('available','quarantined','expired') DEFAULT 'available',
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_batch_drug FOREIGN KEY (drug_id) REFERENCES drugs(id),
  CONSTRAINT fk_batch_location FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- Purchase orders
CREATE TABLE purchase_orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  po_number VARCHAR(64) UNIQUE,
  created_by INT, -- users.id
  vendor_id INT,
  location_id INT, -- where to deliver
  status ENUM('CREATED','APPROVED','SENT','PARTIAL_RECEIVED','COMPLETED','CANCELLED') DEFAULT 'CREATED',
  total_amount DECIMAL(12,2) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expected_delivery_date DATE,
  CONSTRAINT fk_po_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(id),
  CONSTRAINT fk_po_user FOREIGN KEY (created_by) REFERENCES users(id),
  CONSTRAINT fk_po_location FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- PO items
CREATE TABLE po_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  po_id BIGINT NOT NULL,
  drug_id INT NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10,2),
  CONSTRAINT fk_poitems_po FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
  CONSTRAINT fk_poitems_drug FOREIGN KEY (drug_id) REFERENCES drugs(id)
);

-- Shipments
CREATE TABLE shipments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  po_id BIGINT,
  shipment_number VARCHAR(128) UNIQUE,
  vendor_id INT,
  status ENUM('PENDING','IN_TRANSIT','DELIVERED','RETURNED') DEFAULT 'PENDING',
  tracking_info TEXT,
  shipped_at DATETIME,
  eta DATE,
  received_at DATETIME,
  CONSTRAINT fk_ship_po FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
  CONSTRAINT fk_ship_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

-- Shipment items (what's shipped)
CREATE TABLE shipment_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  shipment_id BIGINT NOT NULL,
  drug_id INT NOT NULL,
  quantity INT NOT NULL,
  CONSTRAINT fk_shipitems_ship FOREIGN KEY (shipment_id) REFERENCES shipments(id),
  CONSTRAINT fk_shipitems_drug FOREIGN KEY (drug_id) REFERENCES drugs(id)
);

-- Receive notes (GRN)
CREATE TABLE receive_notes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  shipment_id BIGINT,
  received_by INT, -- users.id
  location_id INT,
  received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  remarks TEXT,
  CONSTRAINT fk_receive_ship FOREIGN KEY (shipment_id) REFERENCES shipments(id),
  CONSTRAINT fk_receive_user FOREIGN KEY (received_by) REFERENCES users(id),
  CONSTRAINT fk_receive_location FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- Receive items (creates or updates drug_batch)
CREATE TABLE receive_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  receive_note_id BIGINT NOT NULL,
  drug_id INT NOT NULL,
  batch_no VARCHAR(128),
  quantity INT NOT NULL,
  unit_cost DECIMAL(10,2),
  manufacture_date DATE,
  expiry_date DATE,
  CONSTRAINT fk_recitems_receive FOREIGN KEY (receive_note_id) REFERENCES receive_notes(id),
  CONSTRAINT fk_recitems_drug FOREIGN KEY (drug_id) REFERENCES drugs(id)
);

-- Consumption/disposal logs (dispense)
CREATE TABLE consumption (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  drug_batch_id BIGINT, -- optional, references batch
  drug_id INT NOT NULL,
  location_id INT NOT NULL,
  dispensed_by INT, -- users.id
  patient_id VARCHAR(128) DEFAULT NULL,
  quantity INT NOT NULL,
  reason ENUM('dispense','wastage','lost','return') DEFAULT 'dispense',
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_consumption_batch FOREIGN KEY (drug_batch_id) REFERENCES drug_batch(id),
  CONSTRAINT fk_consumption_drug FOREIGN KEY (drug_id) REFERENCES drugs(id),
  CONSTRAINT fk_consumption_location FOREIGN KEY (location_id) REFERENCES locations(id),
  CONSTRAINT fk_consumption_user FOREIGN KEY (dispensed_by) REFERENCES users(id)
);

-- Forecasts (ML output)
CREATE TABLE demand_forecasts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  drug_id INT NOT NULL,
  location_id INT NOT NULL,
  forecast_date DATE NOT NULL, -- date that forecast is for
  forecast_quantity INT,
  model_version VARCHAR(64),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_forecast_drug FOREIGN KEY (drug_id) REFERENCES drugs(id),
  CONSTRAINT fk_forecast_location FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- Audit log
CREATE TABLE audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  action VARCHAR(255),
  entity_type VARCHAR(100),
  entity_id VARCHAR(64),
  details TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id)
);