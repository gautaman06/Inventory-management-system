from flask import Flask,request,redirect,render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import func
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///frappe.db'
db = SQLAlchemy(app)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),nullable=False)

    def __repr__(self):
        return '<Product %r>' %self.id

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer,primary_key=True)
    name= db.Column(db.String(50))

    def __repr__(self):
        return '<Location %r>' %self.id

class Movement(db.Model):
    movement_id= db.Column(db.Integer,primary_key=True)
    product_id= db.Column(db.Integer,db.ForeignKey('product.id'))
    product = db.relationship("Product")
    to_location_id = db.Column(db.Integer,db.ForeignKey('location.id'))
    to_location =   db.relationship("Location",primaryjoin=to_location_id==Location.id)
    from_location_id = db.Column(db.Integer,db.ForeignKey('location.id'))
    from_location = db.relationship("Location",primaryjoin=from_location_id==Location.id)
    quantity = db.Column(db.Integer)

    def __repr__(self):
        return '<Movement %r>' %self.id


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/products',methods=["GET","POST"])
def products():
    if request.method == "GET":
        products = Product.query.all()
        return render_template('products.html',products=products)
    if request.method == "POST":
        product_name = request.form["product-name"]
        new_product = Product(name=product_name)

        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect('/products')
        except:
            return "Database error"

@app.route('/products/<int:id>/update',methods=["GET","POST"])
def update_product(id):
    product = Product.query.get_or_404(id)
    if request.method == "GET":
        return render_template("update_product.html",product=product)
    if request.method == "POST":
        product.name = request.form['product-name']

        try:
            db.session.commit()
            return redirect('/products')
        except:
            return "Database error"

@app.route('/locations',methods=["GET","POST"])
def locations():
    if request.method == "GET":
        locations = Location.query.all()
        return render_template('locations.html',locations=locations)
    if request.method == "POST":
        location_name = request.form["location-name"]
        new_location = Location(name=location_name)

        try:
            db.session.add(new_location)
            db.session.commit()
            return redirect('/locations')
        except:
            return "Database error"

@app.route('/locations/<int:id>/update',methods=["GET","POST"])
def update_locations(id):
    location = Location.query.get_or_404(id)
    if request.method == "GET":
        return render_template("update_location.html",location=location)
    if request.method == "POST":
        location.name = request.form['location-name']

        try:
            db.session.commit()
            return redirect('/locations')
        except:
            return "Database error"

@app.route('/movements',methods=["GET","POST"])
def movements():
    if request.method == "GET":
        products = Product.query.all()
        locations = Location.query.all()
        movements = Movement.query.all()
        return render_template('movements.html',products=products,locations=locations,movements=movements)
    if request.method == "POST":
        to_location = request.form['to-location']
        from_location = request.form['from-location']
        product = request.form['product']
        quantity = request.form['quantity']
        if from_location == 'none':
            new_movement = Movement(to_location_id=to_location,from_location_id=from_location\
                ,product_id=product,quantity=quantity)
            try:
                db.session.add(new_movement)
                db.session.commit()
                return redirect('/movements')
            except:
                return "Database error"
        else:
            quantity_at_location = get_quantity(from_location,product)
            if quantity_at_location < int(quantity):
                return "Not enough quantity is available"
            else:
                new_movement = Movement(to_location_id=to_location,from_location_id=from_location\
                ,product_id=product,quantity=quantity)
                try:
                    db.session.add(new_movement)
                    db.session.commit()
                    return redirect('/movements')
                except:
                    return "Database error"

@app.route('/report')
def report():
    locations = Location.query.all()
    products = Product.query.all()
    report = []
    
    for location in locations:
        for product in products:
            row = {}
            row["location"] = location.name
            row["product"] = product.name
            row["quantity"] = get_quantity(location.id,product.id)
            report.append(row)
    return render_template('report.html',report=report)

def get_quantity(location,product):
    added_products = Movement.query.\
        filter(Movement.to_location_id==location,Movement.product_id==product)\
            .from_self(func.sum(Movement.quantity,)).all()
    added_products = added_products[0][0]
    if added_products == None:
        added_products = 0
    removed_products = Movement.query.\
        filter(Movement.from_location_id==location,Movement.product_id==product)\
            .from_self(func.sum(Movement.quantity,name="removed")).all()
    removed_products = removed_products[0][0]
    if removed_products == None:
        removed_products = 0
    return added_products-removed_products

@app.route('/movements/<int:id>/update',methods=["GET","POST"])
def update_movements(id):
    movement_to_be_updated = Movement.query.get_or_404(id)
    if request.method == "GET":
        products = Product.query.all()
        locations = Location.query.all()
        movements = Movement.query.all()
        return render_template('update_movements.html',products=products,locations=locations,movement=movement_to_be_updated)
    if request.method == "POST":
        movement_to_be_updated.to_location_id = request.form["to_location"]
        movement_to_be_updated.from_location_id = request.form["from_location"]
        movement_to_be_updated.product_id = request.form["product"]
        movement_to_be_updated.quantity = request.form["quantity"] 
        pass

if __name__ == "__main__":
    app.run(debug=True)