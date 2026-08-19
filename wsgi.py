"""
WSGI entry point para producción.
"""
import os
from app import create_app
from app.extensions import db
from whitenoise import WhiteNoise

config_name = os.getenv("FLASK_ENV", "production")
app = create_app(config_name)

# ✅ Servir archivos estáticos en producción
if os.getenv("FLASK_ENV") == "production":
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=app.static_folder)

# Ejecutar migraciones automáticamente al iniciar
with app.app_context():
    try:
        from flask_migrate import upgrade
        upgrade()
        print("✅ Migraciones aplicadas correctamente")
    except Exception as e:
        print(f"⚠️  Error aplicando migraciones: {e}")

if __name__ == "__main__":
    app.run()