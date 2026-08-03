from pathlib import Path

# Ruta del proyecto actual
BASE = Path(__file__).parent

directorios = [
    "app",
    "app/models",
    "app/blueprints",
    "app/blueprints/main",
    "app/blueprints/shop",
    "app/blueprints/auth",
    "app/blueprints/checkout",
    "app/blueprints/account",
    "app/blueprints/admin",
    "app/services",
    "app/templates",
    "app/templates/macros",
    "app/templates/shop",
    "app/templates/admin",
    "app/templates/emails",
    "app/static",
    "app/static/css",
    "app/static/js",
    "app/static/img",
    "app/utils",
    "migrations",
    "Dockerfile",
    "tests",

]

for carpeta in directorios:
    (BASE / carpeta).mkdir(parents=True, exist_ok=True)

archivos = [
    ".env.example",
    "requirements.txt",
    "pyproject.toml",
    "docker-compose.yml",
    "app/__init__.py",
    "app/extensions.py",
    "app/models/__init__.py",
    "app/models/user.py",
    "app/models/product.py",
    "app/models/order.py",
    "app/models/category.py",
    "app/services/cart_service.py",
    "app/services/payment_service.py",
    "app/services/email_service.py",
   
]

for archivo in archivos:
    ruta = BASE / archivo
    if not ruta.exists():
        ruta.write_text("", encoding="utf-8")

print("Estructura completada.")