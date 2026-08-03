from flask import Blueprint

main_bp = Blueprint('main', __name__)

# Esta línea es OBLIGATORIA para que Flask lea las rutas
from . import routes  # noqa