from flask import Flask
from .extensions import db, login_manager, migrate
from flask_bootstrap import Bootstrap5
import os
from dotenv import load_dotenv
from .models import User
import click
from app.seed import seed_products_from_excel
from pathlib import Path
from flask.cli import with_appcontext 
from werkzeug.security import generate_password_hash

load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # app.config.from_envvar("FLASK_CONFIG", silent=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Fix Render / Postgres "postgres://" → "postgresql://"
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

            app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        else:
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{Path(app.instance_path) / 'app.db'}"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'app.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY", "")
    app.config["STRIPE_WEBHOOK_SECRET"] = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    app.config["ADMIN_EMAILS"] = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS","").split(",") if e.strip()]


    # init extensions
    Bootstrap5(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


    @app.cli.command("init-db")
    def init_db():
        from app import models
        db.create_all()
        click.echo("✅ DB initialized")


    @app.cli.command("seed-products")
    @click.argument("path", required=False)
    def seed_products_cmd(path=None):
        seed_products_from_excel(path or "app/data/products.xlsx")
        click.echo("✅ Products seeded")

        
    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("password")
    @with_appcontext
    def create_admin(email, password):
        user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
        if user:
            user.role = "admin"
        else:
            user = User(
                email=email,
                name="Admin",
                password=generate_password_hash(password, method="pbkdf2:sha256", salt_length=8),
                role="admin",
            )
            db.session.add(user)
        db.session.commit()
        click.echo("✅ Admin ready")

    

    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except:
            return None
    

    # blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.pages import pages_bp
    from .blueprints.shop import shop_bp
    from .blueprints.cart import cart_bp
    from .blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
