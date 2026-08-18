# tests/test_order_status.py
"""Tests de transiciones de estado de órdenes."""
from decimal import Decimal

import pytest

from app.config.constants import OrderStatus
from app.models import Order, OrderItem


def _create_order(session, user, product, status=OrderStatus.PENDING_PAYMENT):
    order = Order(
        user_id=user.id,
        customer_name='Juan Perez',
        customer_email='juan@test.com',
        status=status,
        subtotal=Decimal('100'),
        shipping_cost=Decimal('10'),
        total=Decimal('110'),
        shipping_address='Calle 123',
        shipping_city='Buenos Aires',
        shipping_state='BA',
        shipping_zip='1000',
        shipping_country='Argentina',
    )
    session.add(order); session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        product_sku=product.sku,
        quantity=2,
        price=Decimal('50'),
    )
    session.add(item); session.commit()
    return order


class TestOrderStatusTransitions:
    """Tests de next_statuses (transiciones válidas)."""

    def test_pending_payment_can_pay_or_cancel(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product)
            assert OrderStatus.PAID in order.next_statuses
            assert OrderStatus.CANCELLED in order.next_statuses

    def test_paid_can_prepare_or_cancel(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product, OrderStatus.PAID)
            assert OrderStatus.PREPARING in order.next_statuses
            assert OrderStatus.CANCELLED in order.next_statuses

    def test_shipped_can_deliver(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product, OrderStatus.SHIPPED)
            assert OrderStatus.DELIVERED in order.next_statuses

    def test_delivered_can_complete(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product, OrderStatus.DELIVERED)
            assert OrderStatus.COMPLETED in order.next_statuses

    def test_completed_has_no_transitions(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product, OrderStatus.COMPLETED)
            assert order.next_statuses == []

    def test_cancelled_has_no_transitions(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product, OrderStatus.CANCELLED)
            assert order.next_statuses == []


class TestOrderProperties:
    """Tests de propiedades del modelo Order."""

    def test_status_display_returns_label(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product)
            assert order.status_display  # no vacío
            assert isinstance(order.status_display, str)

    def test_status_icon_returns_emoji(self, app, regular_user, sample_product, session):
        with app.app_context():
            order = _create_order(session, regular_user, sample_product)
            assert order.status_icon  # emoji