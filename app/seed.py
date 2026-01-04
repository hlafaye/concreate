import pandas as pd
from flask import current_app
from app.extensions import db
from app.models import Product
import os
from pathlib import Path


# path = os.path.join(current_app.root_path, "data", "products.xlsx")

def seed_products_from_excel(path: str | None = None):
  
    if path is None:
        path = Path("app/data/products.xlsx")
    else:
        path = Path(path)

    df = pd.read_excel(path)

    for _,row in df.iterrows():
        name = str(row["name"]).strip()
        exists = db.session.execute(db.select(Product).where(Product.name == name)).scalar_one_or_none()
        price = float(row["price"]) if pd.notna(row["price"]) else 0.0


        if exists:
            exists.desc = str(row["desc"]).strip()
            exists.price = str(row["price"]).strip()
            exists.img_path = str(row["img_path"]).strip()
            exists.sku = str(row["sku"]).strip()
            exists.features = str(row["features"]).strip()

        else:
            new_product= Product(name=name,
                                desc = str(row["desc"]).strip(),
                                price = price,
                                img_path = str(row["img_path"]).strip(),
                                sku = str(row["sku"]).strip(),
                                features = str(row["features"]).strip()
                                )
            db.session.add(new_product)
        db.session.commit()