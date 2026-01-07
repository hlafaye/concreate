from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
import stripe

@cart_bp.route("/checkout/success")
def checkout_success():
    session_id = request.args.get("session_id")
    order_id = request.args.get("order_id", type=int)

    if not session_id:
        flash("Missing session_id.", "danger")
        return redirect(url_for("pages.home"))

    # Récupère la session Stripe pour savoir si c’est payé
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

    return render_template("checkout_success.html")
