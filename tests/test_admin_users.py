# tests/test_admin_users.py
# tests/test_admin_users.py
"""
Tests de la gestión de usuarios en el panel admin.
Cubre: listado, filtros, búsqueda, bloquear/desbloquear, dar/quitar rol admin.
"""
from app.models import User


class TestUsersListAccess:
    """Acceso a la lista de usuarios."""

    def test_users_requires_admin(self, auth_client):
        """Un usuario normal NO puede ver la lista de usuarios."""
        resp = auth_client.get('/admin/usuarios', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Usuarios' not in resp.data or b'Solo administradores' in resp.data

    def test_users_list_for_admin(self, admin_client, db, user):
        """Un admin SÍ puede ver la lista de usuarios."""
        resp = admin_client.get('/admin/usuarios')
        assert resp.status_code == 200
        assert user.email.encode() in resp.data

    def test_users_list_includes_self(self, admin_client, db, admin_user):
        """El admin se ve a sí mismo en la lista."""
        resp = admin_client.get('/admin/usuarios')
        assert resp.status_code == 200
        assert admin_user.email.encode() in resp.data


class TestUsersFilters:
    """Filtros de la lista de usuarios."""

    def test_filter_all(self, admin_client, db, user, admin_user):
        resp = admin_client.get('/admin/usuarios?filter=all')
        assert resp.status_code == 200

    def test_filter_admins(self, admin_client, db, user, admin_user):
        resp = admin_client.get('/admin/usuarios?filter=admins')
        assert resp.status_code == 200
        assert admin_user.email.encode() in resp.data
        # El usuario normal no debería aparecer
        assert user.email.encode() not in resp.data

    def test_filter_active(self, admin_client, db, user):
        resp = admin_client.get('/admin/usuarios?filter=active')
        assert resp.status_code == 200
        assert user.email.encode() in resp.data

    def test_filter_blocked_empty(self, admin_client, db, user):
        """Sin usuarios bloqueados, el filtro muestra vacío."""
        resp = admin_client.get('/admin/usuarios?filter=blocked')
        assert resp.status_code == 200


class TestUsersSearch:
    """Búsqueda de usuarios."""

    def test_search_by_email(self, admin_client, db, user):
        resp = admin_client.get(f'/admin/usuarios?q={user.email}')
        assert resp.status_code == 200
        assert user.email.encode() in resp.data

    def test_search_by_name(self, admin_client, db, user):
        resp = admin_client.get('/admin/usuarios?q=Juan')
        assert resp.status_code == 200
        assert user.email.encode() in resp.data

    def test_search_no_results(self, admin_client, db):
        resp = admin_client.get('/admin/usuarios?q=zzzzzzz_inexistente')
        assert resp.status_code == 200
        assert b'No se encontraron' in resp.data


class TestUserDetail:
    """Detalle de usuario."""

    def test_user_detail_loads(self, admin_client, db, user):
        resp = admin_client.get(f'/admin/usuarios/{user.id}')
        assert resp.status_code == 200
        assert user.full_name.encode() in resp.data

    def test_user_detail_404(self, admin_client, db):
        resp = admin_client.get('/admin/usuarios/99999')
        assert resp.status_code == 404


class TestToggleBlock:
    """Bloquear y desbloquear usuarios."""

    def test_block_user(self, admin_client, db, user):
        assert user.is_blocked is False
        resp = admin_client.post(
            f'/admin/usuarios/{user.id}/toggle-block',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(user)
        assert user.is_blocked is True

    def test_unblock_user(self, admin_client, db, user):
        user.is_blocked = True
        db.session.commit()

        resp = admin_client.post(
            f'/admin/usuarios/{user.id}/toggle-block',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(user)
        assert user.is_blocked is False

    def test_cannot_block_self(self, admin_client, db, admin_user):
        """Un admin no puede bloquearse a sí mismo."""
        resp = admin_client.post(
            f'/admin/usuarios/{admin_user.id}/toggle-block',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(admin_user)
        assert admin_user.is_blocked is False

    def test_block_nonexistent_user(self, admin_client, db):
        resp = admin_client.post('/admin/usuarios/99999/toggle-block')
        assert resp.status_code == 404


class TestToggleAdmin:
    """Dar y quitar rol de administrador."""

    def test_give_admin_role(self, admin_client, db, user):
        assert user.is_admin is False
        resp = admin_client.post(
            f'/admin/usuarios/{user.id}/toggle-admin',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(user)
        assert user.is_admin is True

    def test_remove_admin_role(self, admin_client, db):
        """Crear un segundo admin y quitarle el rol."""
        other_admin = User(
            email="otro_admin@test.com",
            first_name="Otro",
            last_name="Admin",
            is_admin=True,
        )
        other_admin.set_password("admin123")
        db.session.add(other_admin)
        db.session.commit()

        resp = admin_client.post(
            f'/admin/usuarios/{other_admin.id}/toggle-admin',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(other_admin)
        assert other_admin.is_admin is False

    def test_cannot_remove_self_admin(self, admin_client, db, admin_user):
        """Un admin no puede quitarse el rol a sí mismo."""
        resp = admin_client.post(
            f'/admin/usuarios/{admin_user.id}/toggle-admin',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(admin_user)
        assert admin_user.is_admin is True

    def test_normal_user_cannot_toggle_admin(self, auth_client, db, user):
        """Un usuario normal no puede dar/quitar rol admin."""
        resp = auth_client.post(
            f'/admin/usuarios/{user.id}/toggle-admin',
            follow_redirects=True
        )
        assert resp.status_code == 200
        db.session.refresh(user)
        assert user.is_admin is False


class TestBlockedUserCannotLogin:
    """Un usuario bloqueado no puede iniciar sesión."""

    def test_blocked_user_login_rejected(self, client, db, user):
        user.is_blocked = True
        db.session.commit()

        resp = client.post('/auth/login', data={
            'email': user.email,
            'password': 'password123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Debe mostrar mensaje de bloqueo
        assert b'bloqueada' in resp.data

    def test_active_user_login_works(self, client, db, user):
        """Un usuario activo SÍ puede hacer login."""
        resp = client.post('/auth/login', data={
            'email': user.email,
            'password': 'password123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Debe haber iniciado sesión correctamente
        resp2 = client.get('/cuenta/')
        assert resp2.status_code == 200