# seed.py
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from werkzeug.security import generate_password_hash

# ---- adapte ces imports à ton projet ----
from app import create_app
from app.extensions import db
from app.models import User, Product, Order, OrderItem  # ajuste les noms
# ----------------------------------------

import os
if os.getenv("DEMO_SEED") != "1":
    raise SystemExit("Set DEMO_SEED=1 to run this script.")

STATUSES = ["paid", "pending", "cancelled"]

def rdate(days_back=45):
    return datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_back), hours=random.randint(0, 23))

def money(x):
    # évite les float chelous
    return Decimal(str(x)).quantize(Decimal("0.01"))

def reset_db(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

def seed_users():
    admin = User(
        name="Admin",
        email="admin@admin.com",
        role="admin",
        password=generate_password_hash("admin"),
    )
    u1 = User(
        name="Demo User",
        email="user@user.com",
        role="user",
        password=generate_password_hash("test"),
    )

    # quelques users random
    extra = []
    for i in range(6):
        extra.append(User(
            name=f"User {i+1}",
            email=f"user{i+1}@demo.com",
            role="user",
            password=generate_password_hash("test"),
        ))

    db.session.add_all([admin, u1, *extra])
    db.session.commit()
    return [admin, u1, *extra]

def seed_products():
    products = [
        Product(
            name="Raw Lamp",
            price=money("340.00"),
            desc="Brutalist concrete cube base, frosted globe.",
            sku="CC-CP-260104-01",
            # si tu stockes une string avec ; :
            img_path="assets/products/prod_3_1.png;assets/products/prod_3_2.png;assets/products/prod_3_3.png;assets/products/prod_3_4.png",
            features="Cast-mineral concrete shell;Modular arc sections;High-density cushions, removable covers;Matte sealed finish (stain-resistant);Floor-safe concealed feet",
        ),
        Product(
            name="Arc Conversation Sofa",
            price=money("2649.00"),
            desc="Modular arc sections, high-density cushions.",
            sku="CC-RT-260104-01",
            img_path="assets/products/prod_1_1.png;assets/products/prod_1_2.png;assets/products/prod_1_3.png;assets/products/prod_1_4.png",
            features="Two-piece reversible layout;Monolithic concrete volume;Chamfered facets for sharp light;Micro-texture sealed top;Anti-slip pads + levelers",
        ),
        Product(
            name="Cut-X Coffee Table",
            price=money("1054.00"),
            desc="Offset X silhouette, mineral concrete finish.",
            sku="CC-FA-260212-01",
            img_path="assets/products/prod_2_1.png;assets/products/prod_2_2.png;assets/products/prod_2_3.png;assets/products/prod_2_4.png",
            features="Two-piece reversible layout;Monolithic concrete volume;Chamfered facets for sharp light;Micro-texture sealed top;Anti-slip pads + levelers",
        ),
    ]

    db.session.add_all(products)
    db.session.commit()
    return products

def seed_orders(users, products, n=18):
    # On crée des commandes réalistes avec 1 à 3 items
    for _ in range(n):
        user = random.choice([u for u in users if u.role != "admin"])
        status = random.choices(STATUSES, weights=[0.55, 0.30, 0.15])[0]
        created_at = rdate()

        order = Order(
        user_id=user.id,
        email=user.email,          # ✅ obligatoire chez toi
        status=status,
        created_at=created_at,
        subtotal=0.0,              # ✅ si NOT NULL
        shipping=0.0,              # ✅ si NOT NULL
        tax=0.0,                   # ✅ si NOT NULL
        total=0.0,                 # ✅ sera recalculé
    )
        

        db.session.add(order)
        db.session.flush()  # pour avoir order.id avant les items

        k = random.randint(1, 3)
        chosen = random.sample(products, k=k)
        total = Decimal("0.00")
        
        total_items = Decimal("0.00")

        for p in chosen:
            qty = random.randint(1, 2)
            
            line_total = (Decimal(str(p.price)) * qty).quantize(Decimal("0.01"))
            total += line_total

            line_total = Decimal(p.price) * qty
            total_items += line_total

            item = OrderItem(
                order_id=order.id,
                product_id=p.id,
                qty=qty,
                # snapshots si tu utilises ça
                name_snapshot=p.name,
                sku_snapshot=p.sku,
                unit_price=p.price,
                line_total=line_total,
            )
            db.session.add(item)
        

        

        order.subtotal = total_items
        order.shipping = Decimal("0.00")
        order.tax = Decimal("0.00")
        order.total = (order.subtotal + order.shipping + order.tax).quantize(
            Decimal("0.01")
)



        order.total = total.quantize(Decimal("0.01"))

    db.session.commit()

def main():
    app = create_app()
    reset_db(app)

    with app.app_context():
        users = seed_users()
        products = seed_products()
        seed_orders(users, products, n=22)

        print("✅ DB seeded.")
        print("Admin: admin@admin.com / admin")
        print("User : user@user.com / test")

if __name__ == "__main__":
    main()
