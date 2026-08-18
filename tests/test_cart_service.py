# tests/test_cart_service.py
"""
Tests del carrito de compras (servicio basado en sesión de Flask).

El fixture `db` deja un app_context activo; el carrito además necesita
un request_context. Las mutaciones de stock/active se commitean ANTES
de abrir el request_context para que el carrito las vea.
"""
from decimal import Decimal

from app.models import Product
from app.services.cart_service import Cart


class TestCartAdd:
    def test_add_new_product(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            assert cart.add(sample_product.id, 2) is True
            assert cart.total_items == 2
            assert cart.total_price == Decimal('100.00')

    def test_add_accumulates_quantity(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.add(sample_product.id, 3)
            assert cart.total_items == 5

    def test_add_respects_stock_limit(self, app, db, sample_product):
        sample_product.stock = 3
        db.session.commit()
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 10)
            assert cart.total_items == 3

    def test_add_inactive_product_returns_false(self, app, db, sample_product):
        sample_product.active = False
        db.session.commit()
        with app.test_request_context():
            cart = Cart()
            assert cart.add(sample_product.id, 1) is False
            assert cart.total_items == 0

    def test_add_nonexistent_product_returns_false(self, app, db):
        with app.test_request_context():
            cart = Cart()
            assert cart.add(9999, 1) is False


class TestCartRemove:
    def test_remove_existing(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.remove(sample_product.id)
            assert cart.total_items == 0

    def test_remove_nonexistent_is_noop(self, app, db):
        with app.test_request_context():
            cart = Cart()
            cart.remove(9999)  # no debe fallar
            assert cart.total_items == 0


class TestCartUpdate:
    def test_update_quantity(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.update(sample_product.id, 5)
            assert cart.total_items == 5

    def test_update_to_zero_removes(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.update(sample_product.id, 0)
            assert cart.total_items == 0

    def test_update_to_none_removes(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.update(sample_product.id, None)
            assert cart.total_items == 0

    def test_update_respects_stock(self, app, db, sample_product):
        sample_product.stock = 4
        db.session.commit()
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 1)
            cart.update(sample_product.id, 10)
            assert cart.total_items == 4


class TestCartClear:
    def test_clear_empties_cart(self, app, sample_product, expensive_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.add(expensive_product.id, 1)
            assert cart.total_items == 3
            cart.clear()
            assert cart.total_items == 0
            assert cart.total_price == Decimal('0')


class TestCartItemsProperty:
    def test_items_includes_subtotal(self, app, sample_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 3)
            items = cart.items
            assert items[0]['subtotal'] == Decimal('150.00')
            assert items[0]['quantity'] == 3

    def test_items_skips_inactive_products(self, app, db, sample_product, expensive_product):
        with app.test_request_context():
            cart = Cart()
            cart.add(sample_product.id, 2)
            cart.add(expensive_product.id, 1)
            assert cart.total_items == 3

            # Desactivar usando la sesión activa en ESTE contexto
            prod = db.session.get(Product, expensive_product.id)
            prod.active = False
            db.session.commit()

            items = cart.items
            assert len(items) == 1
            assert items[0]['product'].id == sample_product.id