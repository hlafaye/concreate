from flask import session, redirect, url_for, request, flash, render_template, current_app, Response
from . import cart_bp
from app.extensions import db 
from app.models import Product, Order, OrderItem
from flask_login import current_user
import stripe

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

@cart_bp.route("/checkout", methods=["POST"])
def checkout():

    cart = session.get("cart", {})
    if not cart:
        flash("Cart is empty", "error")
        return redirect(url_for("cart.cart_view"))

    ids = [int(pid) for pid in cart.keys()]
    products = db.session.execute(
        db.select(Product).where(Product.id.in_(ids))
    ).scalars().all()
    prod_by_id = {p.id: p for p in products}

    # 2) calc totals
    items_payload = []
    subtotal = 0.0

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = prod_by_id.get(pid)
        if not p:
            continue
        line_total = float(p.price) * int(qty)
        subtotal += line_total
        items_payload.append((p, int(qty), line_total))

    shipping = 680.00
    TAX_RATE = 0.10  # 10%
    tax = subtotal * TAX_RATE
    total = subtotal + shipping + tax

    # 3) créer Order
    order = Order(
        user_id=current_user.id if current_user.is_authenticated else None,
        email=current_user.email if current_user.is_authenticated else "guest@concreate.local",
        status="pending",
        subtotal=subtotal,
        shipping=shipping,
        tax=tax,
        total=total,
    )
    db.session.add(order)
    db.session.flush()  # => order.id dispo

    # 4) créer OrderItems
    for p, qty, line_total in items_payload:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=p.id,
            sku_snapshot=p.sku,
            name_snapshot=p.name,
            unit_price=float(p.price),
            qty=qty,
            line_total=line_total,
        ))

    db.session.commit()

     # 3) Stripe session
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    success_url = (
            url_for("cart.checkout_success", _external=True)
            + "?order_id=" + str(order.id)
            + "&session_id={CHECKOUT_SESSION_ID}"
        )
    cancel_url  = url_for("cart.cart_view", _external=True)

    stripe_session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": p.name},
                    "unit_amount": int(float(p.price) * 100),
                },
                "quantity": qty,
            }
            for p, qty, _ in items_payload
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"order_id": str(order.id)},
    )

    return redirect(stripe_session.url, code=303)

@cart_bp.route("/checkout/success")
def checkout_success():
    session_id = request.args.get("session_id")
    order_id = request.args.get("order_id", type=int)
    if not session_id:
        flash("Missing session_id.", "danger")
        return redirect(url_for("pages.home"))

    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    s = stripe.checkout.Session.retrieve(session_id)

    # Stripe: payment_status = "paid" quand c’est OK
    if s.payment_status == "paid":
        order = db.session.get(Order, order_id) if order_id else None

        # sécurité : si order_id pas passé, on peut fallback metadata
        if not order and s.metadata and s.metadata.get("order_id"):
            order = db.session.get(Order, int(s.metadata["order_id"]))

        if order:
            order.status = "paid"
            order.stripe_session_id = session_id  # si tu as ce champ (reco)
            db.session.commit()

        # vider le panier côté session
        session.pop("cart", None)

        flash("Payment confirmed ✅", "success")
    else:
        flash("Payment not completed yet.", "warning")

    # 👇 adapte l’endpoint à ton projet
    return redirect(url_for("auth.order_detail", order_id=order.id))


@cart_bp.route("/checkout/cancel")
def checkout_cancel():
    order_id = request.args.get("order_id")
    if order_id:
        order = db.session.get(Order, int(order_id))
        if order and order.status == "pending":
            order.status = "cancelled"
            db.session.commit()
    flash("Payment cancelled.", "warning")
    return redirect(url_for("cart.cart_view"))



@cart_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    endpoint_secret = current_app.config["STRIPE_WEBHOOK_SECRET"]

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception:
        return Response(status=400)

    etype = event["type"]
    obj = event["data"]["object"]

    def set_status_from_metadata(new_status: str):
        order_id = (obj.get("metadata") or {}).get("order_id")
        if not order_id:
            return
        order = db.session.get(Order, int(order_id))
        if not order:
            return
        order.status = new_status
        db.session.commit()

    if etype in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        # paiement OK
        set_status_from_metadata("paid")

    elif etype == "checkout.session.async_payment_failed":
        set_status_from_metadata("cancelled")

    # (optionnel) tu peux gérer refunds plus tard

    return Response(status=200)
