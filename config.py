import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = "SimpleCache"

    # URL pública del sitio (links de email, webhook MP y callback OAuth)
    PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5000")

    # Subida de imágenes
    UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "img" / "products")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB total
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # Galería de imágenes por producto
    MAX_EXTRA_IMAGES = 8
    MAX_IMAGE_SIZE_MB = 5

    # Email
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "Marroquinería Artesanal <marroquineriapeluzza@gmail.com>"
    )

    # Email del administrador para recibir alertas de nuevos pedidos
    ADMIN_EMAIL = os.getenv(
        "ADMIN_EMAIL",
        os.getenv("MAIL_USERNAME", "marroquineriapeluzza@gmail.com")
    )

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Login social (OAuth)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

    # Dominio público (CRÍTICO para el redirect_uri de OAuth)
    PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5000")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'dev.db'}"
    )
    MAIL_SUPPRESS_SEND = False


class ProductionConfig(Config):
    DEBUG = False

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url and db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    STATIC_URL = "/static/"
    STATIC_ROOT = str(BASE_DIR / "staticfiles")
    PREFERRED_URL_SCHEME = "https"


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    SERVER_NAME = "localhost.test"