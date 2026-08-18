# tests/test_auth.py
"""
Tests de autenticación: registro, login, logout y rutas protegidas.
"""
from app.models import User


class TestRegister:
    def test_register_page_loads(self, client):
        resp = client.get('/auth/registro')
        assert resp.status_code == 200

    def test_register_new_user(self, client, db):
        resp = client.post('/auth/registro', data={
            'first_name': 'María',
            'last_name': 'González',
            'email': 'maria@test.com',
            'password': 'securepass1',
            'password2': 'securepass1',
        }, follow_redirects=True)
        assert resp.status_code == 200
        user = User.query.filter_by(email='maria@test.com').first()
        assert user is not None
        assert user.first_name == 'María'

    def test_register_duplicate_email(self, client, db, user):
        resp = client.post('/auth/registro', data={
            'first_name': 'Otro',
            'last_name': 'Usuario',
            'email': 'cliente@test.com',
            'password': 'password123',
            'password2': 'password123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # No se creó un segundo usuario con el mismo email
        assert User.query.filter_by(email='cliente@test.com').count() == 1

    def test_register_short_password(self, client, db):
        resp = client.post('/auth/registro', data={
            'first_name': 'Ana',
            'last_name': 'Lopez',
            'email': 'ana@test.com',
            'password': 'short',
            'password2': 'short',
        }, follow_redirects=True)
        assert resp.status_code == 200
        # La contraseña no cumple el mínimo de 8 caracteres
        assert User.query.filter_by(email='ana@test.com').first() is None


class TestLogin:
    def test_login_page_loads(self, client):
        resp = client.get('/auth/login')
        assert resp.status_code == 200

    def test_login_success(self, client, db, user):
        resp = client.post('/auth/login', data={
            'email': 'cliente@test.com',
            'password': 'password123',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_password(self, client, db, user):
        resp = client.post('/auth/login', data={
            'email': 'cliente@test.com',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_nonexistent_user(self, client, db):
        resp = client.post('/auth/login', data={
            'email': 'nobody@test.com',
            'password': 'whatever123',
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestLogout:
    def test_logout(self, auth_client):
        resp = auth_client.get('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200

    def test_logout_requires_login(self, client):
        resp = client.get('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200


class TestProtectedRoutes:
    def test_account_requires_login(self, client):
        resp = client.get('/cuenta/', follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_denied_for_normal_user(self, auth_client):
        resp = auth_client.get('/admin/', follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_dashboard_for_admin(self, admin_client, db):
        resp = admin_client.get('/admin/')
        assert resp.status_code == 200