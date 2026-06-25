CREATE TABLE IF NOT EXISTS suppliers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    email        TEXT NOT NULL,
    phone        TEXT NOT NULL DEFAULT '',
    address      TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    sku         TEXT NOT NULL UNIQUE,
    category    TEXT NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 0,
    min_stock   INTEGER NOT NULL DEFAULT 10,
    price       REAL NOT NULL DEFAULT 0,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    description TEXT DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    quantity     INTEGER NOT NULL,
    unit_price   REAL NOT NULL,
    total_amount REAL NOT NULL,
    notes        TEXT DEFAULT '',
    sale_date    TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO suppliers (id,name,contact_name,email,phone,address) VALUES
(1,'TechParts Inc.','Alice Johnson','alice@techparts.com','+1-555-0101','123 Industrial Ave, Chicago, IL'),
(2,'Global Supplies Co.','Bob Martinez','bob@globalsupplies.com','+1-555-0102','456 Commerce St, New York, NY'),
(3,'Prime Electronics','Carol White','carol@primeelec.com','+1-555-0103','789 Tech Blvd, San Jose, CA'),
(4,'FreshGoods Ltd.','David Lee','david@freshgoods.com','+1-555-0104','321 Market Rd, Austin, TX');

INSERT OR IGNORE INTO products (id,name,sku,category,quantity,min_stock,price,supplier_id) VALUES
(1,'Laptop Pro 15','LAP-001','Electronics',45,10,1299.99,3),
(2,'Wireless Mouse','MOU-001','Electronics',8,20,29.99,1),
(3,'Mechanical Keyboard','KEY-001','Electronics',5,15,89.99,1),
(4,'Monitor 27-inch 4K','MON-001','Electronics',22,8,449.99,3),
(5,'Office Chair Ergonomic','CHR-001','Furniture',12,5,299.99,2),
(6,'Standing Desk','DSK-001','Furniture',7,3,599.99,2),
(7,'Notebook A4 Pack','NTB-001','Stationery',3,50,12.99,4),
(8,'Webcam HD 1080p','WEB-001','Electronics',2,10,69.99,3),
(9,'Bluetooth Speaker','SPK-001','Electronics',28,10,79.99,1);

INSERT OR IGNORE INTO sales (id,product_id,product_name,quantity,unit_price,total_amount,sale_date) VALUES
(1,1,'Laptop Pro 15',3,1299.99,3899.97,'2026-05-24 03:29:00'),
(2,3,'Mechanical Keyboard',4,89.99,359.96,'2026-05-24 03:29:00'),
(3,4,'Monitor 27-inch 4K',5,449.99,2249.95,'2026-05-24 03:29:00'),
(4,5,'Office Chair Ergonomic',4,299.99,1199.96,'2026-05-24 03:29:00'),
(5,6,'Standing Desk',2,599.99,1199.98,'2026-05-24 03:30:00');
