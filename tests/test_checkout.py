# tests/test_checkout.py
"""
Tests del flujo de carrito y checkout (rutas HTTP).
"""


class TestCartRoutes:
    def test_cart_requires_login(self, client, db):
        resp = client.get('/checkout/carrito', follow_redirects=True)
        assert resp.status_code == 200

    def test_cart_empty(self, auth_client):
        resp = auth_client.get('/checkout/carrito')
        assert resp.status_code == 200

    def test_add_to_cart(self, auth_client, db, product):
        resp = auth_client.post(
            f'/checkout/agregar/{product.id}',
            data={'quantity': 1},
            follow_redirects=True
        )
        assert resp.status_code == 200

    def test_remove_from_cart(self, auth_client, db, product):
        auth_client.post(f'/checkout/agregar/{product.id}', data={'quantity': 1})
        resp = auth_client.post(
            f'/checkout/carrito/remove/{product.id}',
            follow_redirects=True
        )
        assert resp.status_code == 200


class TestCheckoutRoutes:
    def test_checkout_redirects_empty_cart(self, auth_client):
        resp = auth_client.get('/checkout/checkout', follow_redirects=True)
        assert resp.status_code == 200

    def test_checkout_with_items(self, auth_client, db, product):
        auth_client.post(f'/checkout/agregar/{product.id}', data={'quantity': 1})
        resp = auth_client.get('/checkout/checkout')
        assert resp.status_code == 200


class TestCouponRoutes:
    def test_apply_valid_coupon(self, auth_client, db, coupon, product):
        auth_client.post(f'/checkout/agregar/{product.id}', data={'quantity': 1})
        resp = auth_client.post(
            '/checkout/aplicar-cupon',
            data={'code': 'TEST10'},
            follow_redirects=True
        )
        assert resp.status_code == 200

    def test_apply_invalid_coupon(self, auth_client, db, product):
        auth_client.post(f'/checkout/agregar/{product.id}', data={'quantity': 1})
        resp = auth_client.post(
            '/checkout/aplicar-cupon',
            data={'code': 'INVALIDO'},
            follow_redirects=True
        )
        assert resp.status_code == 200


class TestPaymentPages:
    def test_success_page(self, client, db):
        resp = client.get('/checkout/pago/exitoso/999')
        assert resp.status_code == 404

    def test_pending_page(self, client, db):
        resp = client.get('/checkout/pago/pendiente/999')
        assert resp.status_code == 404

    def test_failure_page(self, client, db):
        resp = client.get('/checkout/pago/fallido/999')
        assert resp.status_code == 404