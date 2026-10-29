"""Demo master data: suppliers, catalog items and cost centers (all amounts in CHF)."""

SUPPLIERS = [
    ("SUP-001", "Alpine IT Distribution AG", "orders@alpine-it.example"),
    ("SUP-002", "Rhein Tech Trading GmbH", "sales@rheintech.example"),
    ("SUP-003", "Helvetic Office Supplies AG", "order@helvetic-office.example"),
    ("SUP-004", "Medion", "procurement@medion.example"),
    ("SUP-005", "MediaMarkt", "business@mediamarkt.example"),
]

BASE_CATALOG_ITEMS = [
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

# Four supplier offers for each of these 25 products provide 100 additional
# internal catalog records and exercise cheapest-offer selection.
EXPANDED_PRODUCTS = [
    ("BL14", "Business Laptop 14", "Laptop", "950.00", 30),
    ("BL15", "Business Laptop 15", "Laptop", "1020.00", 25),
    ("ULTRA13", "Ultrabook 13", "Laptop", "1250.00", 20),
    ("GAMING15", "Gaming Laptop 15", "Laptop", "1450.00", 12),
    ("USB-C-MON", "USB-C Monitor 27", "Monitor", "280.00", 35),
    ("OFF-MON24", "Office Monitor 24", "Monitor", "160.00", 40),
    ("DOCK-USB", "USB-C Docking Station", "Accessories", "145.00", 50),
    ("WEBCAM-HD", "HD Conference Webcam", "Accessories", "75.00", 80),
    ("HEADSET", "Business Headset", "Accessories", "65.00", 100),
    ("KEYBOARD", "Wireless Office Keyboard", "Accessories", "45.00", 100),
    ("MOUSE-WL", "Wireless Office Mouse", "Accessories", "25.00", 120),
    ("LASER-MOUSE", "Laser Presentation Mouse", "Accessories", "38.00", 60),
    ("USB-HUB", "USB-C Hub 7 Port", "Accessories", "52.00", 75),
    ("CHAIR-MESH", "Mesh Office Chair", "Furniture", "245.00", 18),
    ("DESK-120", "Standing Desk 120", "Furniture", "520.00", 10),
    ("DESK-160", "Standing Desk 160", "Furniture", "680.00", 8),
    ("DRAWER", "Mobile Office Drawer", "Furniture", "135.00", 25),
    ("WHITEBOARD", "Magnetic Whiteboard 120", "Furniture", "180.00", 15),
    ("TONER-BLK", "Laser Printer Toner Black", "Office Supplies", "92.00", 40),
    ("TONER-COLOR", "Laser Printer Toner Color", "Office Supplies", "118.00", 35),
    ("PAPER-REC", "Recycled Copy Paper 500 sheets", "Office Supplies", "7.20", 500),
    ("NOTEBOOK", "A5 Business Notebook", "Office Supplies", "4.50", 300),
    ("PEN-SET", "Executive Pen Set", "Office Supplies", "12.00", 200),
    ("CABLE-HDMI", "HDMI Cable 2m", "Accessories", "14.00", 150),
    ("POWER-STRIP", "Office Power Strip", "Accessories", "29.00", 90),
]

OFFER_SUPPLIERS = ("SUP-004", "SUP-005", "SUP-001", "SUP-002")
OFFER_MARKUPS = ("120.00", "0.00", "180.00", "90.00")

CATALOG_ITEMS = BASE_CATALOG_ITEMS + [
    (
        f"{supplier}-{code}",
        name,
        category,
        supplier,
        f"{float(price) + float(markup):.2f}",
        stock,
    )
    for code, name, category, price, stock in EXPANDED_PRODUCTS
    for supplier, markup in zip(OFFER_SUPPLIERS, OFFER_MARKUPS)
]

COST_CENTERS = [
    ("CC-100", "IT Department", "50000.00"),
    ("CC-200", "Marketing", "8000.00"),
    ("CC-300", "Facilities", "3000.00"),
]
