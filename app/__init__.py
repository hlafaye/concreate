from flask import Flask
from .extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_envvar("FLASK_CONFIG", silent=True)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)

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
