import os

from flask import Flask, send_from_directory
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

def create_app(config_overrides=None) -> Flask:

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

    if config_overrides:
        app.config.update(config_overrides)

    # Ensure upload folder is absolute regardless of current working directory.
    if not os.path.isabs(app.config["UPLOAD_FOLDER"]):
        backend_root = os.path.dirname(os.path.dirname(__file__))
        app.config["UPLOAD_FOLDER"] = os.path.abspath(
            os.path.join(backend_root, app.config["UPLOAD_FOLDER"])
        )

    # -----------------------------------------------
    # Initialize Extensions
    # -----------------------------------------------

    init_extensions(app)

    # -----------------------------------------------
    # Register Blueprints / APIs
    # -----------------------------------------------

    register_routes(app)
    register_static_routes(app)

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


def register_static_routes(app: Flask):

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        print(app.config["UPLOAD_FOLDER"])
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


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