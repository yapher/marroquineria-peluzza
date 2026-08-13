from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='../../templates/admin')

# Importar todas las rutas desde el módulo routes
from .routes import *  # noqa