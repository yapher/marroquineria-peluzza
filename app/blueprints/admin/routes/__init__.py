# app/blueprints/admin/routes/__init__.py
"""
Módulo de rutas del panel de administración.
Cada funcionalidad está separada en su propio archivo para mejor mantenibilidad.
"""
from flask import request
from flask_login import login_required, current_user
from functools import wraps

from .. import admin_bp


# ============================================
# DECORADORES Y FUNCIONES AUXILIARES
# ============================================

def admin_required(f):
    """Decorador que verifica si el usuario es administrador."""
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            from flask import flash, redirect, url_for
            flash("Acceso restringido. Solo administradores.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapper


def _get_bool(field_name):
    """Lee booleanos del POST. Un checkbox desmarcado NO se envía."""
    return field_name in request.form


# ============================================
# IMPORTAR TODAS LAS RUTAS
# ============================================

from . import dashboard
from . import products
from . import categories
from . import orders
from . import coupons
from . import stats
from . import reviews