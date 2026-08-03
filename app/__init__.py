import os
from flask import Flask

# 1. Importar extensiones PRIMERO
from .extensions import db, migrate, login_manager, csrf, mail, cache


def create_app(config_name='development'):
    app = Flask(__name__)
    
    # 2. Cargar configuración
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    # 3. Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    cache.init_app(app)

    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # 4. Registrar Blueprints
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

    # 5. Flask-Login: User Loader (¡Aquí sí funciona porque login_manager ya se inicializó!)
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        """Le dice a Flask-Login cómo cargar un usuario desde la base de datos."""
        return User.query.get(int(user_id))

    # 6. Context Processor (Variables globales para todos los templates)
    @app.context_processor
    def inject_globals():
        from .services.cart_service import Cart
        context = {
            "cart_count": Cart().total_items if Cart().total_items > 0 else 0,
        }
        return context

    # 7. Comandos CLI personalizados
    from .cli import seed_command, create_admin_command
    app.cli.add_command(seed_command)
    app.cli.add_command(create_admin_command)

    return app