import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'invcontrol-secret-2024')
DATABASE = os.path.join(os.path.dirname(__file__), 'invcontrol.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
        conn.executescript(f.read())
    conn.commit(); conn.close()

if not os.path.exists(DATABASE):
    init_db()

# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.route('/')
def dashboard():
    conn = get_db()
    total_products  = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_suppliers = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
    total_revenue   = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales").fetchone()[0]
    low_stock_count = conn.execute("SELECT COUNT(*) FROM products WHERE quantity < min_stock").fetchone()[0]
    sales_by_cat    = conn.execute("""
        SELECT p.category, COALESCE(SUM(s.total_amount),0) AS revenue
        FROM products p LEFT JOIN sales s ON s.product_id = p.id
        GROUP BY p.category ORDER BY revenue DESC
    """).fetchall()
    stock_levels = conn.execute("""
        SELECT name, quantity, min_stock,
               CASE WHEN quantity=0 THEN 'out'
                    WHEN quantity < min_stock THEN 'low' ELSE 'ok' END AS status
        FROM products ORDER BY quantity ASC LIMIT 10
    """).fetchall()
    conn.close()
    return render_template('dashboard.html',
        total_products=total_products, total_suppliers=total_suppliers,
        total_revenue=total_revenue, low_stock_count=low_stock_count,
        sales_by_cat=sales_by_cat, stock_levels=stock_levels)

# ── Products ───────────────────────────────────────────────────────────────────
@app.route('/products')
def products():
    conn = get_db()
    products  = conn.execute("SELECT p.*, s.name AS supplier_name FROM products p LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.name").fetchall()
    suppliers = conn.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
    conn.close()
    return render_template('products.html', products=products, suppliers=suppliers)

@app.route('/products/add', methods=['POST'])
def add_product():
    name=request.form['name'].strip(); sku=request.form['sku'].strip().upper()
    category=request.form['category'].strip()
    quantity=int(request.form.get('quantity',0)); min_stock=int(request.form.get('min_stock',10))
    price=float(request.form.get('price',0)); supplier_id=request.form.get('supplier_id') or None
    if not name or not sku or not category:
        flash('Name, SKU, and Category are required.','error'); return redirect(url_for('products'))
    conn = get_db()
    try:
        conn.execute("INSERT INTO products (name,sku,category,quantity,min_stock,price,supplier_id) VALUES (?,?,?,?,?,?,?)",
                     (name,sku,category,quantity,min_stock,price,supplier_id))
        conn.commit(); flash(f'Product "{name}" added!','success')
    except sqlite3.IntegrityError:
        flash(f'SKU "{sku}" already exists.','error')
    finally: conn.close()
    return redirect(url_for('products'))

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    conn = get_db()
    row = conn.execute("SELECT name FROM products WHERE id=?", (id,)).fetchone()
    if row:
        conn.execute("DELETE FROM products WHERE id=?", (id,)); conn.commit()
        flash(f'Deleted "{row["name"]}".','success')
    conn.close(); return redirect(url_for('products'))

# ── Suppliers ──────────────────────────────────────────────────────────────────
@app.route('/suppliers')
def suppliers():
    conn = get_db()
    suppliers = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    conn.close(); return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/add', methods=['POST'])
def add_supplier():
    name=request.form['name'].strip(); contact_name=request.form['contact_name'].strip()
    email=request.form['email'].strip(); phone=request.form.get('phone','').strip()
    address=request.form.get('address','').strip()
    if not name or not contact_name or not email:
        flash('Name, Contact, and Email are required.','error'); return redirect(url_for('suppliers'))
    conn = get_db()
    conn.execute("INSERT INTO suppliers (name,contact_name,email,phone,address) VALUES (?,?,?,?,?)",
                 (name,contact_name,email,phone,address))
    conn.commit(); conn.close(); flash(f'Supplier "{name}" added!','success')
    return redirect(url_for('suppliers'))

@app.route('/suppliers/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    conn = get_db()
    row = conn.execute("SELECT name FROM suppliers WHERE id=?", (id,)).fetchone()
    if row:
        conn.execute("DELETE FROM suppliers WHERE id=?", (id,)); conn.commit()
        flash(f'Deleted "{row["name"]}".','success')
    conn.close(); return redirect(url_for('suppliers'))

# ── Sales ──────────────────────────────────────────────────────────────────────
@app.route('/sales')
def sales():
    conn = get_db()
    sales    = conn.execute("SELECT * FROM sales ORDER BY sale_date DESC").fetchall()
    products = conn.execute("SELECT id,name,quantity,price FROM products WHERE quantity>0 ORDER BY name").fetchall()
    total    = sum(s['total_amount'] for s in sales)
    conn.close(); return render_template('sales.html', sales=sales, products=products, total_revenue=total)

@app.route('/sales/add', methods=['POST'])
def add_sale():
    product_id=int(request.form['product_id']); quantity=int(request.form.get('quantity',1))
    notes=request.form.get('notes','').strip()
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not product: flash('Product not found.','error'); conn.close(); return redirect(url_for('sales'))
    if quantity > product['quantity']:
        flash(f'Only {product["quantity"]} units in stock.','error'); conn.close(); return redirect(url_for('sales'))
    total = quantity * product['price']
    conn.execute("INSERT INTO sales (product_id,product_name,quantity,unit_price,total_amount,notes) VALUES (?,?,?,?,?,?)",
                 (product_id,product['name'],quantity,product['price'],total,notes))
    conn.execute("UPDATE products SET quantity=quantity-? WHERE id=?", (quantity,product_id))
    conn.commit(); conn.close(); flash('Sale recorded!','success')
    return redirect(url_for('sales'))

# ── Low Stock ──────────────────────────────────────────────────────────────────
@app.route('/low-stock')
def low_stock():
    conn = get_db()
    items = conn.execute("""
        SELECT *, CASE WHEN quantity=0 OR CAST(quantity AS REAL)/min_stock<=0.3
                       THEN 'CRITICAL' ELSE 'REORDER SOON' END AS urgency
        FROM products WHERE quantity < min_stock
        ORDER BY CAST(quantity AS REAL)/min_stock ASC
    """).fetchall()
    conn.close(); return render_template('low_stock.html', items=items)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
