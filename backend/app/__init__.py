import os

from flask import Flask
from flask_cors import CORS
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail

from config import DevelopmentConfig, ProductionConfig

from app.models import db
from app.jwt_config import jwt_manager


# --------------------------------------------------
# Extensions
# --------------------------------------------------

migrate = Migrate()
csrf = CSRFProtect()
cache = Cache()
mail = Mail()


# --------------------------------------------------
# Application Factory
# --------------------------------------------------

def create_app() -> Flask:

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # -----------------------------------------------
    # Load Configuration
    # -----------------------------------------------

    env = os.getenv("FLASK_ENV", "development")

    if env == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # -----------------------------------------------
    # Initialize Extensions
    # -----------------------------------------------

    init_extensions(app)

    # -----------------------------------------------
    # Register Blueprints / APIs
    # -----------------------------------------------

    register_routes(app)

    return app


# --------------------------------------------------
# Extensions Initialization
# --------------------------------------------------

def init_extensions(app: Flask):

    CORS(
        app,
        origins=["*"],
        supports_credentials=True
    )

    db.init_app(app)

    migrate.init_app(
        app,
        db,
        render_as_batch=True
    )

    jwt_manager.init_app(app)

    csrf.init_app(app)

    cache.init_app(app)

    mail.init_app(app)


# --------------------------------------------------
# Routes / APIs
# --------------------------------------------------

def register_routes(app: Flask):

    from app.api import init_app

    init_app(app)


# --------------------------------------------------
# Exposed Objects
# --------------------------------------------------

from app.models import UserRole

__all__ = [
    "db",
    "csrf",
    "cache",
    "mail",
    "UserRole",
]