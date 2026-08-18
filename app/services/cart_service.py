# app/services/cart_service.py
"""
Carrito de compras (persistido en sesión).

⚠️ La validación de stock para el checkout vive en
checkout_service.validate_cart_stock() (única fuente de verdad).
"""
from flask import session

from ..models import Product
from ..extensions import db


class Cart:
    def __init__(self):
        if "cart" not in session:
            session["cart"] = {}

    def add(self, product_id: int, quantity: int = 1) -> bool:
        """Agrega un producto respetando el stock disponible."""
        product = db.session.get(Product, product_id)
        if not product or not product.active:
            return False

        pid = str(product_id)
        current = session["cart"].get(pid, {}).get("quantity", 0)
        new_quantity = min(current + quantity, product.stock)  # tope de stock
        if new_quantity <= 0:
            return False

        session["cart"][pid] = {"quantity": new_quantity}
        session.modified = True
        return True

    def remove(self, product_id: int):
        """Quita un producto del carrito."""
        pid = str(product_id)
        if pid in session["cart"]:
            del session["cart"][pid]
            session.modified = True

    def update(self, product_id: int, quantity: int):
        """Actualiza cantidad. Robusto ante None o productos inexistentes."""
        pid = str(product_id)
        if pid not in session["cart"]:
            return

        if quantity is None or quantity <= 0:
            self.remove(product_id)
            return

        # no permitir más que el stock
        product = db.session.get(Product, product_id)
        if product:
            quantity = min(quantity, product.stock)
        if quantity <= 0:
            self.remove(product_id)
            return

        session["cart"][pid]["quantity"] = quantity
        session.modified = True

    def clear(self):
        """Vacía el carrito por completo."""
        session["cart"] = {}
        session.modified = True

    @property
    def items(self):
        """Lista de ítems válidos del carrito (producto activo)."""
        cart_items = []
        for pid, data in session["cart"].items():
            product = db.session.get(Product, int(pid))
            if product and product.active:
                cart_items.append({
                    "product": product,
                    "quantity": data["quantity"],
                    "subtotal": product.price * data["quantity"]
                })
        return cart_items

    @property
    def total_items(self):
        """Cantidad total de unidades en el carrito."""
        return sum(item["quantity"] for item in self.items)

    @property
    def total_price(self):
        """Subtotal del carrito (sin envío ni descuentos)."""
        return sum(item["subtotal"] for item in self.items)