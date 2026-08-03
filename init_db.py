"""
Script para inicializar la base de datos en producción.
Ejecuta migraciones y crea datos iniciales si es necesario.
"""
import os
from app import create_app
from app.extensions import db

app = create_app(os.getenv("FLASK_ENV", "production"))

def init_database():
    """Inicializa la base de datos."""
    with app.app_context():
        # Ejecutar migraciones
        from flask_migrate import upgrade
        upgrade()
        
        print("✅ Base de datos inicializada correctamente")

if __name__ == "__main__":
    init_database()