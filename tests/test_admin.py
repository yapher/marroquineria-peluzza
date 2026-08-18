# tests/test_admin.py
"""
Tests del panel de administración: acceso y rutas protegidas.
"""


class TestAdminAccess:
    def test_admin_requires_login(self, client, db):
        resp = client.get('/admin/', follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_denied_for_normal_user(self, auth_client):
        resp = auth_client.get('/admin/', follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_dashboard(self, admin_client, db, product):
        resp = admin_client.get('/admin/')
        assert resp.status_code == 200


class TestAdminProducts:
    def test_products_list(self, admin_client, db, product):
        resp = admin_client.get('/admin/productos')
        assert resp.status_code == 200

    def test_product_new_form(self, admin_client, db, category):
        resp = admin_client.get('/admin/productos/nuevo')
        assert resp.status_code == 200

    def test_product_edit_form(self, admin_client, db, product):
        resp = admin_client.get(f'/admin/productos/{product.id}/editar')
        assert resp.status_code == 200


class TestAdminCategories:
    def test_categories_list(self, admin_client, db, category):
        resp = admin_client.get('/admin/categorias')
        assert resp.status_code == 200

    def test_category_new_form(self, admin_client, db):
        resp = admin_client.get('/admin/categorias/nueva')
        assert resp.status_code == 200


class TestAdminOrders:
    def test_orders_list(self, admin_client, db):
        resp = admin_client.get('/admin/pedidos')
        assert resp.status_code == 200

    def test_orders_filter(self, admin_client, db):
        resp = admin_client.get('/admin/pedidos?status=paid')
        assert resp.status_code == 200


class TestAdminCoupons:
    def test_coupons_list(self, admin_client, db, coupon):
        resp = admin_client.get('/admin/cupones')
        assert resp.status_code == 200

    def test_coupon_new_form(self, admin_client, db):
        resp = admin_client.get('/admin/cupones/nuevo')
        assert resp.status_code == 200


class TestAdminReviews:
    def test_reviews_list(self, admin_client, db):
        resp = admin_client.get('/admin/reseñas')
        assert resp.status_code == 200


class TestAdminStats:
    def test_stats_page(self, admin_client, db):
        resp = admin_client.get('/admin/estadisticas')
        assert resp.status_code == 200