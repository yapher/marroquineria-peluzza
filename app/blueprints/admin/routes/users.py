# app/blueprints/admin/routes/users.py
# app/blueprints/admin/routes/users.py
"""
Rutas para gestión de usuarios en el panel admin.
Permite listar, buscar, filtrar, bloquear/desbloquear y asignar/quitar rol admin.
"""
from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import current_user
from .. import admin_bp
from ....models import User
from ....extensions import db
from ....services.user_service import (
    toggle_block_user,
    toggle_admin_role,
    get_user_stats,
)
from . import admin_required


@admin_bp.route("/usuarios")
@admin_required
def users():
    """Lista todos los usuarios con filtros y búsqueda."""
    filter_type = request.args.get("filter", "all")
    search = request.args.get("q", "").strip()

    query = User.query

    # Filtros por tipo
    if filter_type == "admins":
        query = query.filter_by(is_admin=True)
    elif filter_type == "blocked":
        query = query.filter_by(is_blocked=True)
    elif filter_type == "active":
        query = query.filter_by(is_admin=False, is_blocked=False)

    # Búsqueda por nombre, apellido o email
    if search:
        term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(term))
            | (User.first_name.ilike(term))
            | (User.last_name.ilike(term))
        )

    users_list = query.order_by(User.created_at.desc()).all()
    stats = get_user_stats()

    return render_template(
        "admin/users.html",
        users=users_list,
        stats=stats,
        current_filter=filter_type,
        search=search,
    )


@admin_bp.route("/usuarios/<int:user_id>")
@admin_required
def user_detail(user_id):
    """Detalle completo de un usuario (pedidos, puntos, cuentas sociales)."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    return render_template("admin/user_detail.html", user=user)


@admin_bp.route("/usuarios/<int:user_id>/toggle-block", methods=["POST"])
@admin_required
def user_toggle_block(user_id):
    """Bloquea o desbloquea un usuario."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    success, message = toggle_block_user(user, current_user)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.users"))


@admin_bp.route("/usuarios/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def user_toggle_admin(user_id):
    """Da o quita el rol de administrador."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    success, message = toggle_admin_role(user, current_user)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.users"))