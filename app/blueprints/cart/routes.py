from flask import session, redirect, url_for, request, flash, render_template
from . import cart_bp
from app.extensions import db 
from app.models import Product

@cart_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):

    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", {})
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + qty

    session["cart"] = cart
    session.modified = True
    
    flash("Added to cart", "success")
    return redirect(request.referrer or url_for("pages.home"))


@cart_bp.route("/cart")
def cart_view():
    cart = session.get("cart", {})
    ids = [int(pid) for pid in cart.keys()]

    products = db.session.execute(db.select(Product).where(Product.id.in_(ids))).scalars().all()
    prod_by_id = {p.id: p for p in products}

    items = []
    total = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = prod_by_id.get(pid)
        if not p:
            continue

        line_total = float(p.price) * qty
        total += line_total
        items.append({"product": p, "qty": qty, "line_total": line_total})

    SHIPPING = 680.00 if total > 0 else 0
    TAX_RATE = 0.10  # 10%
    tax = total * TAX_RATE
    total = total + SHIPPING + tax



    return render_template("cart.html",items=items,subtotal=total,shipping=SHIPPING,tax=tax,total=total)



@cart_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def update_qty(product_id):
    cart = session.get("cart", {})
    pid = str(product_id)

    qty = int(request.form.get("qty", 1))
    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = qty

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart.cart_view"))

@cart_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_item(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    flash("Removed from cart", "success")
    return redirect(url_for("cart.cart_view"))