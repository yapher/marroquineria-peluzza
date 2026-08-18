# app/extensions.py
"""
Instancias de extensiones Flask (sin configuración).

⚠️ La configuración de login_manager vive en create_app()
para evitar valores duplicados en dos lugares.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache()
mail = Mail()