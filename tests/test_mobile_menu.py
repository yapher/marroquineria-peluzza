# tests/test_mobile_menu.py
"""
Tests de regresión: el menú móvil incluye el listener de cierre automático
y el evento Alpine correcto.
"""


class TestMobileMenuTemplate:
    """Verifica que el template del menú móvil tenga el cableado correcto."""

    def test_mobile_menu_listens_close_event(self, client, db):
        """El contenedor del menú debe escuchar 'mobile-menu:close'."""
        resp = client.get('/')
        html = resp.data.decode('utf-8')
        assert '@mobile-menu:close.window="mobileMenuOpen = false"' in html

    def test_mobile_menu_panel_exists(self, client, db):
        """El panel del menú móvil debe estar presente."""
        resp = client.get('/')
        html = resp.data.decode('utf-8')
        assert 'mobile-menu-panel' in html

    def test_mobile_menu_js_included(self, client, db):
        """El script mobile-menu.js debe estar incluido en base.html."""
        resp = client.get('/')
        html = resp.data.decode('utf-8')
        assert 'js/mobile-menu.js' in html

    def test_menu_closed_by_default(self, client, db):
        """El body debe inicializar mobileMenuOpen en false."""
        resp = client.get('/')
        html = resp.data.decode('utf-8')
        assert 'x-data="{ mobileMenuOpen: false }"' in html