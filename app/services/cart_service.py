from flask import session
from ..models import Product
from ..extensions import db

class Cart:
    def __init__(self):
        if "cart" not in session:
            session["cart"] = {}

    def add(self, product_id: int, quantity: int = 1):
        pid = str(product_id)
        if pid in session["cart"]:
            session["cart"][pid]["quantity"] += quantity
        else:
            session["cart"][pid] = {"quantity": quantity}
        session.modified = True

    def remove(self, product_id: int):
        pid = str(product_id)
        if pid in session["cart"]:
            del session["cart"][pid]
            session.modified = True

    def update(self, product_id: int, quantity: int):
        pid = str(product_id)
        if quantity > 0:
            session["cart"][pid]["quantity"] = quantity
            session.modified = True
        else:
            self.remove(product_id)

    def clear(self):
        session["cart"] = {}
        session.modified = True

    @property
    def items(self):
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
        return sum(item["quantity"] for item in self.items)

    @property
    def total_price(self):
        return sum(item["subtotal"] for item in self.items)