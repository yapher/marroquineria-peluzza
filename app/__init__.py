# app/__init__.py
"""Factory principal de la aplicación Flask."""
from flask import Flask, flash, redirect, request, url_for
from .extensions import db, migrate, login_manager, csrf, mail, cache, oauth


def create_app(config_name='development'):
    app = Flask(__name__)

    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    oauth.init_app(app)

    # Configuración de login (único lugar, no duplicar en extensions.py)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # ============================================
    # ERROR HANDLERS (deben ir AQUÍ, dentro de create_app)
    # ============================================
    @app.errorhandler(413)
    def request_entity_too_large(e):
        max_mb = app.config.get("MAX_CONTENT_LENGTH", 0) // (1024 * 1024)
        flash(
            f"Los archivos superan el límite de {max_mb} MB en total.",
            "error",
        )
        return redirect(request.referrer or url_for("admin.products"))

    @app.errorhandler(401)
    def unauthorized(e):
        flash('Debes iniciar sesión para acceder a esta página', 'warning')
        return redirect(url_for('auth.login'))

    # ============================================
    # PROVEEDORES OAUTH (Google, Facebook...)
    # ============================================
    from .services.auth.oauth_service import register_providers
    register_providers(app)

    # ============================================
    # BLUEPRINTS
    # ============================================
    from .blueprints.main import main_bp
    from .blueprints.shop import shop_bp
    from .blueprints.auth import auth_bp
    from .blueprints.checkout import checkout_bp
    from .blueprints.account import account_bp
    from .blueprints.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp, url_prefix="/tienda")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    app.register_blueprint(account_bp, url_prefix="/cuenta")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ============================================
    # CONTEXT PROCESSOR (variables globales de templates)
    # ============================================
    @app.context_processor
    def inject_globals():
        from .services.cart_service import Cart
        from .models import Category
        from .services.auth.oauth_service import get_enabled_providers

        cart = Cart()

        # Categorías activas para el menú (mobile + desktop)
        try:
            nav_categories = Category.query.filter_by(active=True).order_by(Category.name).all()
        except Exception:
            nav_categories = []

        return {
            "cart_count": cart.total_items,
            "nav_categories": nav_categories,
            "social_providers": get_enabled_providers(),
        }

    from .cli import seed_command, create_admin_command
    app.cli.add_command(seed_command)
    app.cli.add_command(create_admin_command)

    return app