from functools import wraps
from flask import abort, current_app, redirect, url_for, flash, request, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Order, Product
from . import admin_bp
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import selectinload
import json

def first_img(image_field):
    if not image_field:
        return None
    if isinstance(image_field, list):
        return image_field[0] if image_field else None
    # string -> essayer JSON
    try:
        arr = json.loads(image_field)
        if isinstance(arr, list) and arr:
            return arr[0]
    except Exception:
        pass
    return None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        allowed = set(current_app.config.get("ADMIN_EMAILS", []))
        if (current_user.email or "").lower() not in allowed:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route("/admin/orders")
@login_required
@admin_required
def admin_dashboard():
    products=db.session.execute(db.select(Product)).scalars().all()
    products_by_id = {p.id: p for p in products}


    orders = (
    Order.query
    .options(selectinload(Order.items))
    .order_by(Order.created_at.desc())
    .all()
    )

    # dates par défaut: 30 derniers jours
    date_from_str = request.args.get("from")
    date_to_str = request.args.get("to")

    if date_to_str:
        date_to = datetime.fromisoformat(date_to_str)
    else:
        date_to = datetime.utcnow()

    if date_from_str:
        date_from = datetime.fromisoformat(date_from_str)
    else:
        date_from = date_to - timedelta(days=30)

    q = Order.query.filter(Order.created_at >= date_from, Order.created_at <= date_to)

    # KPI
    total_orders = q.count()
    total_revenue = q.with_entities(func.coalesce(func.sum(Order.total), 0.0)).scalar()
    avg_basket = (total_revenue / total_orders) if total_orders else 0.0
    unique_customers = q.with_entities(func.count(func.distinct(Order.email))).scalar()

    # Pie status
    status_rows = (
        q.with_entities(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    status_labels = [r[0] for r in status_rows]
    status_counts = [r[1] for r in status_rows]

    # CA par jour
    daily_rows = (
        q.with_entities(func.date(Order.created_at), func.coalesce(func.sum(Order.total), 0.0))
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    daily_labels = [str(r[0]) for r in daily_rows]
    daily_totals = [float(r[1]) for r in daily_rows]
    

    return render_template("admin_dashboard.html",
        orders=orders,
        products_by_id=products_by_id, 
        date_from=date_from.date().isoformat(),
        date_to=date_to.date().isoformat(),
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        avg_basket=float(avg_basket),
        unique_customers=int(unique_customers),
        status_labels=status_labels,
        status_counts=status_counts,
        daily_labels=daily_labels,
        daily_totals=daily_totals,)


@admin_bp.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get("status", "")
    if new_status not in ("pending", "paid", "cancelled"):
        abort(400)

    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    order.status = new_status
    db.session.commit()
    flash(f"Order #{order.id} updated → {new_status}", "success")
    return redirect(url_for("admin.admin_dashboard"))

