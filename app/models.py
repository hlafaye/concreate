from flask_login import UserMixin
from .extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float


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
    