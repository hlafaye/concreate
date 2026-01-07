from flask_login import UserMixin
from .extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, Date, DateTime
from datetime import datetime, timezone


class User(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    role = db.Column(db.String(20), default="user")


class Product(db.Model):
    __tablename__="products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    desc: Mapped[str] = mapped_column(String(1000),nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    img_path: Mapped[str] = mapped_column(String(1000),nullable=False)
    sku: Mapped[str] = mapped_column(String(1000),nullable=False)
    features: Mapped[str] = mapped_column(String(1000),nullable=False)

ORDER_STATUSES = ("pending", "paid", "cancelled")

def set_status(self, new_status: str):
    if new_status not in ORDER_STATUSES:
        raise ValueError("Invalid order status")
    self.status = new_status

class Order(db.Model):
    __tablename__="orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int|None] = mapped_column(Integer, nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(1000),nullable=False, default="pending")
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    shipping: Mapped[float] = mapped_column(Float, nullable=False)
    tax: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.now(timezone.utc))
    items = relationship("OrderItem",backref="order",cascade="all, delete-orphan")


    

class OrderItem(db.Model):
    __tablename__="order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("products.id"), nullable=False)
    sku_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[float] = mapped_column(Float, nullable=False)
