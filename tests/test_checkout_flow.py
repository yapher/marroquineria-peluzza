# tests/test_checkout_flow.py
"""Tests del flujo de checkout (sin llamar a MP real)."""
from decimal import Decimal

import pytest

from app.services.cart_service import Cart
from tests.conftest import login_user


class TestCartAccess:
    def test_cart_requires_login(self, client):
        response = client.get('/checkout/carrito', follow_redirects=False)
        assert response.status_code in (302, 401)

    def test_cart_page_loads_for_logged_user(self, client, regular_user):
        login_user(client, regular_user)
        response = client.get('/checkout/carrito')
        assert response.status_code == 200


class TestCheckoutPage:
    def test_checkout_redirects_if_cart_empty(self, client, regular_user):
        login_user(client, regular_user)
        response = client.get('/checkout/checkout', follow_redirects=True)
        assert response.status_code == 200
        assert b'vac' in response.data.lower()  # "vacío"

    def test_checkout_loads_with_items(self, client, regular_user, sample_product, app):
        login_user(client, regular_user)
        with client.session_transaction() as sess:
            sess['cart'] = {str(sample_product.id): {'quantity': 1}}
        response = client.get('/checkout/checkout')
        assert response.status_code == 200
        assert sample_product.name.encode() in response.data