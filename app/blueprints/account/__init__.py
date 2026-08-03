# app/blueprints/account/__init__.py
from flask import Blueprint

account_bp = Blueprint('account', __name__, template_folder='../../templates/account')

# Esta línea es OBLIGATORIA para que Flask lea las rutas
from . import routes  # noqa