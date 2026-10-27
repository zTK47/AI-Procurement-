# Data model

SQLite database `procurement.db`, mapped with the SQLAlchemy ORM in
[`src/app/infrastructure/db.py`](../src/app/infrastructure/db.py).
DDL: [`schema.sql`](schema.sql). Recreate the database with demo data:

```bash
.venv/bin/python scripts/init_db.py --reset
```

## Entity-relationship diagram

![ER diagram](data-model.png)

Source (renders on GitHub):

```mermaid
erDiagram
    SUPPLIERS ||--o{ CATALOG_ITEMS : "offers"
    SUPPLIERS ||--o{ PURCHASE_ORDERS : "receives"
    COST_CENTERS ||--o{ PROCUREMENT_REQUESTS : "funds"
    COST_CENTERS ||--o{ PURCHASE_ORDERS : "is charged"
    CATALOG_ITEMS |o--o{ PROCUREMENT_REQUESTS : "resolved to"
    CATALOG_ITEMS ||--o{ PURCHASE_ORDER_LINES : "ordered as"
    PROCUREMENT_REQUESTS ||--|{ REQUEST_STATUS_HISTORY : "records"
    PROCUREMENT_REQUESTS ||--o| PURCHASE_ORDERS : "results in"
    PURCHASE_ORDERS ||--|{ PURCHASE_ORDER_LINES : "contains"

    SUPPLIERS {
        varchar id PK
        varchar name
        varchar email
    }
    CATALOG_ITEMS {
        varchar sku PK
        varchar name
        varchar category
        varchar supplier_id FK
        numeric unit_price
        varchar currency
        int stock
    }
    COST_CENTERS {
        varchar id PK
        varchar name
        numeric budget_remaining
        varchar currency
    }
    PROCUREMENT_REQUESTS {
        varchar id PK
        varchar raw_text "user prompt"
        varchar requester_name
        varchar cost_center_id FK
        varchar status
        datetime created_at
        int parsed_quantity "LLM output"
        varchar parsed_product "LLM output"
        varchar parsed_category "LLM output"
        float parsed_confidence "LLM output"
        varchar sku FK "resolved item"
        numeric unit_price "price snapshot"
        numeric total
        varchar budget_check
        varchar stock_check
        varchar approval_level
        varchar rejection_reason
    }
    REQUEST_STATUS_HISTORY {
        int id PK
        varchar request_id FK
        int position
        varchar status
        datetime changed_at
    }
    PURCHASE_ORDERS {
        varchar po_number PK
        varchar request_id FK "unique"
        varchar supplier_id FK
        varchar cost_center_id FK
        datetime created_at
    }
    PURCHASE_ORDER_LINES {
        int id PK
        varchar po_number FK
        varchar sku FK
        varchar description
        int quantity
        numeric unit_price
        varchar currency
    }
```

## Relationships

| From | To | Cardinality | Meaning |
|---|---|---|---|
| Supplier | CatalogItem | 1 : n | A supplier offers many catalog items |
| CostCenter | ProcurementRequest | 1 : n | Every request is charged to one cost center |
| CatalogItem | ProcurementRequest | 0..1 : n | A request resolves to the cheapest matching item (empty if rejected early) |
| ProcurementRequest | RequestStatusHistory | 1 : 1..n | Audit trail of every workflow state |
| ProcurementRequest | PurchaseOrder | 1 : 0..1 | Created when the order is sent |
| Supplier | PurchaseOrder | 1 : n | The order goes to the item's supplier |
| CostCenter | PurchaseOrder | 1 : n | Budget is consumed on send |
| PurchaseOrder | PurchaseOrderLine | 1 : 1..n | Order positions |
| CatalogItem | PurchaseOrderLine | 1 : n | Each line references a catalog SKU |

Prices on requests and order lines are snapshots, so later catalog price
changes do not alter historic orders.
