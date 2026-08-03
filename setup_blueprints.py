# setup_blueprints.py
import os

# 1. Crear directorios de blueprints y plantillas
dirs = [
    "app/blueprints/main",
    "app/blueprints/shop",
    "app/blueprints/auth",
    "app/blueprints/checkout",
    "app/blueprints/account",
    "app/blueprints/admin",
    "app/templates",
    "app/static/css",
    "app/static/js",
    "app/static/img",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# 2. Contenido mínimo para que los imports funcionen
files = {
    "app/blueprints/main/__init__.py": "from flask import Blueprint\nmain_bp = Blueprint('main', __name__)\nfrom . import routes  # noqa",
    "app/blueprints/main/routes.py": "from flask import render_template\nfrom . import main_bp\n\n@main_bp.route('/')\ndef index():\n    return '<h1 style=\"font-family:sans-serif;text-align:center;margin-top:50px;\">👜 Marroquinería Artesanal - ¡Funciona! 🚀</h1>'",
    
    "app/blueprints/shop/__init__.py": "from flask import Blueprint\nshop_bp = Blueprint('shop', __name__)\nfrom . import routes  # noqa",
    "app/blueprints/shop/routes.py": "from . import shop_bp\n\n@shop_bp.route('/')\ndef catalog():\n    return 'Catálogo de productos'",
    
    "app/blueprints/auth/__init__.py": "from flask import Blueprint\nauth_bp = Blueprint('auth', __name__)\nfrom . import routes  # noqa",
    "app/blueprints/auth/routes.py": "from . import auth_bp\n\n@auth_bp.route('/login')\ndef login():\n    return 'Página de Login'",
    
    "app/blueprints/checkout/__init__.py": "from flask import Blueprint\ncheckout_bp = Blueprint('checkout', __name__)\nfrom . import routes  # noqa",
    "app/blueprints/checkout/routes.py": "from . import checkout_bp\n\n@checkout_bp.route('/')\ndef cart():\n    return 'Carrito de compras'",
    
    "app/blueprints/account/__init__.py": "from flask import Blueprint\naccount_bp = Blueprint('account', __name__)\nfrom . import routes  # noqa",
    "app/blueprints/account/routes.py": "from . import account_bp\n\n@account_bp.route('/')\ndef profile():\n    return 'Perfil de usuario'",
    
    "app/blueprints/admin/__init__.py": "from flask import Blueprint\nadmin_bp = Blueprint('admin', __name__)\nfrom . import routes  # noqa",
    "app/blueprints/admin/routes.py": "from . import admin_bp\n\n@admin_bp.route('/')\ndef dashboard():\n    return 'Panel de Administración'",
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ ¡Estructura de blueprints creada exitosamente!")