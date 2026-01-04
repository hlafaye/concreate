from flask import Flask
from .extensions import db, login_manager
from flask_bootstrap import Bootstrap5
import os
from dotenv import load_dotenv
from .models import User

load_dotenv()

def create_app():
    app = Flask(__name__)
    # app.config.from_envvar("FLASK_CONFIG", silent=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{app.instance_path}/concreate.db'


    Bootstrap5(app)
    # init extensions
    db.init_app(app)
    login_manager.init_app(app)

    
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
