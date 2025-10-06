from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import click
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# secret key for flashing messages (simple)
app.config['SECRET_KEY'] = 'dev-key-change-me'

db = SQLAlchemy(app)

# --- Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Product {self.sku} {self.name}>"

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)

    def __repr__(self):
        return f"<Location {self.code} {self.name}>"

class ProductMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    to_location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    from_location = db.relationship('Location', foreign_keys=[from_location_id], backref='out_movements')
    to_location = db.relationship('Location', foreign_keys=[to_location_id], backref='in_movements')
    product = db.relationship('Product', backref='movements')

    def __repr__(self):
        return f"<Move {self.id} {self.product.name} {self.qty}>"

# --- Routes: Products ---
@app.route('/')
def index():
    return redirect(url_for('view_products'))

@app.route('/products')
def view_products():
    products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET','POST'])
def add_product():
    if request.method == 'POST':
        sku = request.form['sku'].strip()
        name = request.form['name'].strip()
        desc = request.form.get('description','').strip()
        if not sku or not name:
            flash('SKU and Name required', 'danger')
            return redirect(url_for('add_product'))
        if Product.query.filter_by(sku=sku).first():
            flash('SKU already exists', 'danger')
            return redirect(url_for('add_product'))
        p = Product(sku=sku, name=name, description=desc)
        db.session.add(p)
        db.session.commit()
        flash('Product added', 'success')
        return redirect(url_for('view_products'))
    return render_template('product_form.html', action='Add', product=None)

@app.route('/products/edit/<int:product_id>', methods=['GET','POST'])
def edit_product(product_id):
    p = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        p.sku = request.form['sku'].strip()
        p.name = request.form['name'].strip()
        p.description = request.form.get('description','').strip()
        db.session.commit()
        flash('Product updated', 'success')
        return redirect(url_for('view_products'))
    return render_template('product_form.html', action='Edit', product=p)

@app.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted', 'success')
    return redirect(url_for('view_products'))

# --- Routes: Locations ---
@app.route('/locations')
def view_locations():
    locations = Location.query.order_by(Location.name).all()
    return render_template('locations.html', locations=locations)

@app.route('/locations/add', methods=['GET','POST'])
def add_location():
    if request.method == 'POST':
        code = request.form['code'].strip()
        name = request.form['name'].strip()
        address = request.form.get('address','').strip()
        if not code or not name:
            flash('Code and Name required', 'danger')
            return redirect(url_for('add_location'))
        if Location.query.filter_by(code=code).first():
            flash('Location code exists', 'danger')
            return redirect(url_for('add_location'))
        loc = Location(code=code, name=name, address=address)
        db.session.add(loc)
        db.session.commit()
        flash('Location added', 'success')
        return redirect(url_for('view_locations'))
    return render_template('location_form.html', action='Add', location=None)

@app.route('/locations/edit/<int:location_id>', methods=['GET','POST'])
def edit_location(location_id):
    loc = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        loc.code = request.form['code'].strip()
        loc.name = request.form['name'].strip()
        loc.address = request.form.get('address','').strip()
        db.session.commit()
        flash('Location updated', 'success')
        return redirect(url_for('view_locations'))
    return render_template('location_form.html', action='Edit', location=loc)

@app.route('/locations/delete/<int:location_id>', methods=['POST'])
def delete_location(location_id):
    loc = Location.query.get_or_404(location_id)
    db.session.delete(loc)
    db.session.commit()
    flash('Location deleted', 'success')
    return redirect(url_for('view_locations'))

# --- Routes: Movements ---
@app.route('/movements')
def view_movements():
    movements = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).limit(200).all()
    return render_template('movements.html', movements=movements)

@app.route('/movements/add', methods=['GET','POST'])
def add_movement():
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        qty = int(request.form['qty'])
        from_location_id = request.form.get('from_location_id') or None
        to_location_id = request.form.get('to_location_id') or None
        if from_location_id == '': from_location_id = None
        if to_location_id == '': to_location_id = None
        if not product_id or qty == 0:
            flash('Product and non-zero qty required', 'danger')
            return redirect(url_for('add_movement'))
        # convert to ints if provided
        from_id = int(from_location_id) if from_location_id else None
        to_id = int(to_location_id) if to_location_id else None
        mv = ProductMovement(product_id=product_id, qty=qty, from_location_id=from_id, to_location_id=to_id)
        db.session.add(mv)
        db.session.commit()
        flash('Movement recorded', 'success')
        return redirect(url_for('view_movements'))
    return render_template('movement_form.html', products=products, locations=locations)

@app.route('/movements/delete/<int:movement_id>', methods=['POST'])
def delete_movement(movement_id):
    m = ProductMovement.query.get_or_404(movement_id)
    db.session.delete(m)
    db.session.commit()
    flash('Movement deleted', 'success')
    return redirect(url_for('view_movements'))

# --- Reports: Balance per product per location ---
@app.route('/report/balance')
def report_balance():
    # Fetch all products and locations
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()

    # Initialize dictionary product_id -> {location_id -> 0}
    balances = {}
    for p in products:
        balances[p.id] = {loc.id: 0 for loc in locations}

    # Iterate movements and update balances
    all_movements = ProductMovement.query.order_by(ProductMovement.timestamp).all()
    for mv in all_movements:
        pid = mv.product_id
        q = mv.qty
        # If movement has to_location -> add
        if mv.to_location_id:
            balances.setdefault(pid, {})
            balances[pid].setdefault(mv.to_location_id, 0)
            balances[pid][mv.to_location_id] += q
        # If movement has from_location -> subtract
        if mv.from_location_id:
            balances.setdefault(pid, {})
            balances[pid].setdefault(mv.from_location_id, 0)
            balances[pid][mv.from_location_id] -= q

    # Build a list of rows for display: product, location, qty (skip zeros)
    rows = []
    for p in products:
        for loc in locations:
            qty = balances.get(p.id, {}).get(loc.id, 0)
            if qty != 0:
                rows.append({
                    'product': p,
                    'location': loc,
                    'qty': qty
                })
    # Sort rows for nicer display
    rows = sorted(rows, key=lambda r: (r['product'].name, r['location'].name))
    return render_template('report_balance.html', rows=rows, products=products, locations=locations)

# --- CLI commands to setup and seed DB ---
@app.cli.command("init-db")
def init_db():
    """Create database tables."""
    db.create_all()
    click.echo("Database initialized (inventory.db)")

@app.cli.command("seed")
def seed():
    """Seed the db with sample products, locations and movements."""
    db.create_all()
    # clear
    ProductMovement.query.delete()
    Product.query.delete()
    Location.query.delete()
    db.session.commit()

    # create products
    p1 = Product(sku='PROD-A', name='Product A', description='Sample product A')
    p2 = Product(sku='PROD-B', name='Product B', description='Sample product B')
    p3 = Product(sku='PROD-C', name='Product C', description='Sample product C')
    p4 = Product(sku='PROD-D', name='Product D', description='Sample product D')

    # create locations
    l1 = Location(code='WH-1', name='Warehouse 1', address='100 Main St')
    l2 = Location(code='WH-2', name='Warehouse 2', address='200 Side St')
    l3 = Location(code='STORE-1', name='Retail Store 1', address='300 Market Rd')
    l4 = Location(code='QUARANTINE', name='Quarantine', address='Holding')

    db.session.add_all([p1,p2,p3,p4,l1,l2,l3,l4])
    db.session.commit()

    # make ~20 movements (some ins, outs, transfers)
    moves = [
        # add inventory to warehouses
        (None, l1.id, p1.id, 50),
        (None, l1.id, p2.id, 30),
        (None, l2.id, p1.id, 20),
        (None, l3.id, p3.id, 15),
        (None, l2.id, p4.id, 40),
        (None, l1.id, p3.id, 25),
        (None, l3.id, p2.id, 10),

        # transfers
        (l1.id, l2.id, p1.id, 10),
        (l2.id, l3.id, p4.id, 5),
        (l1.id, l3.id, p3.id, 3),

        # move out (to no location)
        (l3.id, None, p3.id, 2),
        (l2.id, None, p4.id, 7),

        # more movements
        (None, l1.id, p4.id, 8),
        (l1.id, l4.id, p2.id, 5),
        (l4.id, l1.id, p2.id, 2),
        (None, l3.id, p1.id, 6),
        (l3.id, l2.id, p1.id, 1),
        (l2.id, l1.id, p1.id, 4),
        (None, l4.id, p4.id, 10),
        (l4.id, None, p4.id, 1),
    ]
    for frm, to, pid, q in moves:
        mv = ProductMovement(from_location_id=frm, to_location_id=to, product_id=pid, qty=q)
        db.session.add(mv)
    db.session.commit()
    click.echo("Seeded sample products, locations and ~20 movements")

if __name__ == "__main__":
    app.run(debug=True)
