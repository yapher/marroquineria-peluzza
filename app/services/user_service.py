# app/services/user_service.py
# app/services/user_service.py
"""
Servicio de gestión de usuarios (panel admin).
Centraliza las operaciones de bloquear/desbloquear y asignar/quitar rol admin,
con validaciones de seguridad (un admin no puede modificarse a sí mismo).
"""
from ..extensions import db
from ..models import User


class UserActionError(Exception):
    """Error de negocio al intentar una acción sobre un usuario."""
    pass


def toggle_block_user(user: User, admin: User) -> tuple[bool, str]:
    """
    Bloquea o desbloquea un usuario.
    Devuelve (success, message).

    Reglas:
    - Un admin no puede bloquearse a sí mismo.
    - Un admin no puede bloquear a otro admin (protección adicional).
    """
    if user.id == admin.id:
        return False, "❌ No podés bloquearte a vos mismo"

    if user.is_admin and not admin.is_admin:
        return False, "❌ No tenés permisos para modificar otro administrador"

    user.is_blocked = not user.is_blocked
    db.session.commit()

    action = "bloqueado" if user.is_blocked else "desbloqueado"
    return True, f"✅ Usuario {user.email} {action}"


def toggle_admin_role(user: User, admin: User) -> tuple[bool, str]:
    """
    Da o quita el rol de administrador.
    Devuelve (success, message).

    Reglas:
    - Un admin no puede quitarse el rol a sí mismo (evita dejar el sistema sin admins).
    """
    if user.id == admin.id:
        return False, "❌ No podés quitarte el rol de administrador a vos mismo"

    user.is_admin = not user.is_admin
    db.session.commit()

    if user.is_admin:
        message = f"✅ {user.email} ahora es administrador"
    else:
        message = f"✅ {user.email} ya no es administrador"
    return True, message


def get_user_stats() -> dict:
    """Estadísticas rápidas de usuarios para el panel admin."""
    return {
        "total": User.query.count(),
        "admins": User.query.filter_by(is_admin=True).count(),
        "blocked": User.query.filter_by(is_blocked=True).count(),
        "active": User.query.filter_by(is_admin=False, is_blocked=False).count(),
    }