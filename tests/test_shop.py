# tests/test_shop.py
"""
Tests del catálogo de la tienda y detalle de producto.
"""


class TestCatalog:
    def test_catalog_loads(self, client, db, product):
        resp = client.get('/tienda/')
        assert resp.status_code == 200

    def test_catalog_shows_products(self, client, db, product):
        resp = client.get('/tienda/')
        assert b'Billetera' in resp.data

    def test_catalog_filter_category(self, client, db, product):
        resp = client.get('/tienda/?categoria=billeteras')
        assert resp.status_code == 200

    def test_catalog_search(self, client, db, product):
        resp = client.get('/tienda/?q=Billetera')
        assert resp.status_code == 200

    def test_catalog_sort_price(self, client, db, product):
        resp = client.get('/tienda/?sort=price_asc')
        assert resp.status_code == 200

    def test_catalog_htmx(self, client, db, product):
        resp = client.get('/tienda/', headers={'HX-Request': 'true'})
        assert resp.status_code == 200


class TestProductDetail:
    def test_product_page_loads(self, client, db, product):
        resp = client.get('/tienda/producto/billetera-clasica')
        assert resp.status_code == 200
        assert b'Billetera' in resp.data

    def test_product_404(self, client, db):
        resp = client.get('/tienda/producto/no-existe')
        assert resp.status_code == 404


class TestSearchAjax:
    def test_search_returns_results(self, client, db, product):
        resp = client.get('/tienda/buscar?q=Billetera')
        assert resp.status_code == 200

    def test_search_too_short(self, client, db):
        resp = client.get('/tienda/buscar?q=A')
        assert resp.status_code == 200


class TestMainPages:
    def test_index(self, client, db):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_about(self, client, db):
        resp = client.get('/nosotros')
        assert resp.status_code == 200

    def test_shipping(self, client, db):
        resp = client.get('/envios')
        assert resp.status_code == 200

    def test_contact(self, client, db):
        resp = client.get('/contacto')
        assert resp.status_code == 200

    def test_sitemap(self, client, db, product):
        resp = client.get('/sitemap.xml')
        assert resp.status_code == 200
        assert b'xml' in resp.data

    def test_robots(self, client, db):
        resp = client.get('/robots.txt')
        assert resp.status_code == 200