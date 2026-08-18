# tests/test_account.py
"""
Tests de la cuenta de usuario: perfil, pedidos, favoritos.
"""
from app.models import Wishlist


class TestProfile:
    def test_profile_page(self, auth_client):
        resp = auth_client.get('/cuenta/')
        assert resp.status_code == 200

    def test_orders_page(self, auth_client):
        resp = auth_client.get('/cuenta/pedidos')
        assert resp.status_code == 200

    def test_loyalty_page(self, auth_client):
        resp = auth_client.get('/cuenta/fidelizacion')
        assert resp.status_code == 200

    def test_change_password_page(self, auth_client):
        resp = auth_client.get('/cuenta/cambiar-password')
        assert resp.status_code == 200


class TestWishlist:
    def test_wishlist_page(self, auth_client):
        resp = auth_client.get('/cuenta/favoritos')
        assert resp.status_code == 200

    def test_add_to_wishlist(self, auth_client, db, user, product):
        resp = auth_client.post(
            f'/cuenta/favoritos/agregar/{product.id}',
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert Wishlist.query.filter_by(
            user_id=user.id, product_id=product.id
        ).first() is not None

    def test_remove_from_wishlist(self, auth_client, db, user, product):
        auth_client.post(f'/cuenta/favoritos/agregar/{product.id}')
        resp = auth_client.post(
            f'/cuenta/favoritos/quitar/{product.id}',
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert Wishlist.query.filter_by(
            user_id=user.id, product_id=product.id
        ).first() is None

    def test_wishlist_count_endpoint(self, auth_client):
        resp = auth_client.get('/cuenta/favoritos/count')
        assert resp.status_code == 200


class TestChangePassword:
    def test_change_password_success(self, auth_client, db, user):
        resp = auth_client.post('/cuenta/cambiar-password', data={
            'current_password': 'password123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert user.check_password('newpass456') is True

    def test_change_password_wrong_current(self, auth_client, db, user):
        resp = auth_client.post('/cuenta/cambiar-password', data={
            'current_password': 'wrongcurrent',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_change_password_mismatch(self, auth_client, db, user):
        resp = auth_client.post('/cuenta/cambiar-password', data={
            'current_password': 'password123',
            'new_password': 'newpass456',
            'confirm_password': 'differentpass'
        }, follow_redirects=True)
        assert resp.status_code == 200