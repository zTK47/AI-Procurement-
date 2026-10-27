"""Demo master data: suppliers, catalog items and cost centers (all amounts in CHF)."""

SUPPLIERS = [
    ("SUP-001", "Alpine IT Distribution AG", "orders@alpine-it.example"),
    ("SUP-002", "Rhein Tech Trading GmbH", "sales@rheintech.example"),
    ("SUP-003", "Helvetic Office Supplies AG", "order@helvetic-office.example"),
]

CATALOG_ITEMS = [
    ("LEN-T14-G3", "Lenovo ThinkPad T14 Gen 3", "Laptop", "SUP-001", "1200.00", 3),
    ("LEN-X1-C11", "Lenovo ThinkPad X1 Carbon Gen 11", "Laptop", "SUP-002", "1350.00", 20),
    ("DEL-LAT-5440", "Dell Latitude 5440", "Laptop", "SUP-002", "1150.00", 10),
    ("APL-MBA-13", "Apple MacBook Air 13 M3", "Laptop", "SUP-003", "1290.00", 8),
    ("DEL-U2723", "Dell UltraSharp 27 Monitor", "Monitor", "SUP-002", "420.00", 25),
    ("HP-E24-G5", "HP EliteDisplay E24 Monitor", "Monitor", "SUP-001", "210.00", 15),
    ("LOG-MX3S", "Logitech MX Master 3S Mouse", "Accessories", "SUP-003", "89.00", 100),
    ("LOG-MXK", "Logitech MX Keys Keyboard", "Accessories", "SUP-003", "109.00", 60),
    ("OFF-CHAIR-ERG", "Ergonomic Office Chair", "Furniture", "SUP-003", "380.00", 12),
    ("PAP-A4-500", "A4 Copy Paper 500 sheets", "Office Supplies", "SUP-003", "6.50", 1000),
]

COST_CENTERS = [
    ("CC-100", "IT Department", "50000.00"),
    ("CC-200", "Marketing", "8000.00"),
    ("CC-300", "Facilities", "3000.00"),
]
