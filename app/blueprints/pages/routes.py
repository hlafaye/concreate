from flask import Flask, abort, render_template, redirect, url_for, flash
from . import pages_bp
from app.extensions import db 
from app.models import Product



@pages_bp.route("/")
def home():
    products = db.session.execute(db.select(Product)).scalars().all()
    
    return render_template('home.html', products=products)


@pages_bp.route("/contact")
def contact():
    return render_template('contact.html')


@pages_bp.route("/about")
def about():
    return render_template('about.html')


@pages_bp.route("/product/<int:product_id>")
def product(product_id):
    product = db.get_or_404(Product, product_id)
    return render_template('product.html', product=product )





