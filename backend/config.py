from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv()


class Config:
    # ------------------------------------------------
    # CORE APP CONFIG
    # ------------------------------------------------

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    ENV = os.getenv("FLASK_ENV", "development")

    DEBUG = False


    # ------------------------------------------------
    # DATABASE
    # ------------------------------------------------

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # ------------------------------------------------
    # JWT AUTH
    # ------------------------------------------------

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    JWT_TOKEN_LOCATION = ["headers"]

    JWT_HEADER_NAME = "Authorization"

    JWT_HEADER_TYPE = "Bearer"

    # JSON_SORT_KEYS =  False

    # ------------------------------------------------
    # CSRF / SESSION
    # ------------------------------------------------

    WTF_CSRF_ENABLED = False
    WTF_CSRF_SECRET_KEY = SECRET_KEY

    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_DOMAIN = None


    # ------------------------------------------------
    # FILE UPLOADS
    # ------------------------------------------------

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "application/static/upload"
    )

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


    # ------------------------------------------------
    # EMAIL CONFIG
    # ------------------------------------------------

    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME",
        "info@estatepilot.com"
    )

    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

    MAIL_DEFAULT_SENDER = MAIL_USERNAME

    MAIL_USE_TLS = True
    MAIL_USE_SSL = False


    # ------------------------------------------------
    # FRONTEND
    # ------------------------------------------------

    FRONTEND_BASE_URL = os.getenv(
        "FRONTEND_BASE_URL",
        "http://localhost:3000"
    )


    # ------------------------------------------------
    # GOOGLE AUTH (OPTIONAL)
    # ------------------------------------------------

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")



class DevelopmentConfig(Config):

    ENV = "development"

    DEBUG = True

    SESSION_COOKIE_SECURE = False

    FRONTEND_BASE_URL = "http://localhost:3000"



class ProductionConfig(Config):

    ENV = "production"

    DEBUG = False

    SESSION_COOKIE_SECURE = True

    SESSION_COOKIE_SAMESITE = "None"

    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "")