-- Generated from the SQLAlchemy model (src/app/infrastructure/db.py) by scripts/init_db.py
CREATE TABLE suppliers (
	id VARCHAR(20) NOT NULL,
	name VARCHAR(200) NOT NULL,
	email VARCHAR(200) NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE cost_centers (
	id VARCHAR(20) NOT NULL,
	name VARCHAR(200) NOT NULL,
	budget_remaining NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	PRIMARY KEY (id)
);
CREATE TABLE catalog_items (
	sku VARCHAR(40) NOT NULL,
	name VARCHAR(200) NOT NULL,
	category VARCHAR(100) NOT NULL,
	supplier_id VARCHAR(20) NOT NULL,
	unit_price NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	stock INTEGER NOT NULL,
	PRIMARY KEY (sku),
	FOREIGN KEY(supplier_id) REFERENCES suppliers (id)
);
CREATE INDEX ix_catalog_items_category ON catalog_items (category);
CREATE TABLE procurement_requests (
	id VARCHAR(40) NOT NULL,
	raw_text VARCHAR(1000) NOT NULL,
	requester_name VARCHAR(100) NOT NULL,
	cost_center_id VARCHAR(20) NOT NULL,
	status VARCHAR(30) NOT NULL,
	created_at DATETIME NOT NULL,
	parsed_quantity INTEGER,
	parsed_product VARCHAR(200),
	parsed_category VARCHAR(100),
	parsed_confidence FLOAT,
	sku VARCHAR(40),
	unit_price NUMERIC(12, 2),
	total NUMERIC(12, 2),
	currency VARCHAR(3) NOT NULL,
	budget_check VARCHAR(10),
	stock_check VARCHAR(10),
	approval_level VARCHAR(20),
	rejection_reason VARCHAR(200),
	PRIMARY KEY (id),
	FOREIGN KEY(cost_center_id) REFERENCES cost_centers (id),
	FOREIGN KEY(sku) REFERENCES catalog_items (sku)
);
CREATE INDEX ix_procurement_requests_created_at ON procurement_requests (created_at);
CREATE INDEX ix_procurement_requests_status ON procurement_requests (status);
CREATE TABLE request_status_history (
	id INTEGER NOT NULL,
	request_id VARCHAR(40) NOT NULL,
	position INTEGER NOT NULL,
	status VARCHAR(30) NOT NULL,
	changed_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(request_id) REFERENCES procurement_requests (id)
);
CREATE INDEX ix_request_status_history_request_id ON request_status_history (request_id);
CREATE TABLE purchase_orders (
	po_number VARCHAR(40) NOT NULL,
	request_id VARCHAR(40) NOT NULL,
	supplier_id VARCHAR(20) NOT NULL,
	cost_center_id VARCHAR(20) NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (po_number),
	UNIQUE (request_id),
	FOREIGN KEY(request_id) REFERENCES procurement_requests (id),
	FOREIGN KEY(supplier_id) REFERENCES suppliers (id),
	FOREIGN KEY(cost_center_id) REFERENCES cost_centers (id)
);
CREATE TABLE purchase_order_lines (
	id INTEGER NOT NULL,
	po_number VARCHAR(40) NOT NULL,
	sku VARCHAR(40) NOT NULL,
	description VARCHAR(200) NOT NULL,
	quantity INTEGER NOT NULL,
	unit_price NUMERIC(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(po_number) REFERENCES purchase_orders (po_number),
	FOREIGN KEY(sku) REFERENCES catalog_items (sku)
);
CREATE INDEX ix_purchase_order_lines_po_number ON purchase_order_lines (po_number);
