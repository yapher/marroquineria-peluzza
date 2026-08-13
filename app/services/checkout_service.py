# app/services/checkout_service.py
"""
Servicio de Checkout.
Orquesta la creación de órdenes: valida stock, calcula totales,
crea la orden y sus items en la base de datos.

La ruta solo llama a este servicio y maneja la respuesta HTTP.
"""
from flask import current_app
from ..extensions import db
from ..models import Order, OrderItem
from ..config.constants import OrderStatus, DEFAULT_SHIPPING_COST
from .discount_calculator import calculate_all_discounts
from .cart_service import Cart


def validate_cart_stock(cart: Cart) -> tuple[bool, str]:
    """
    Verifica que todos los productos del carrito tengan stock suficiente.
    Devuelve (es_valido, nombre_producto_con_problema).
    """
    for item in cart.items:
        product = item["product"]
        if product.stock < item["quantity"]:
            return False, product.name
    return True, ""


def create_order(
    cart: Cart,
    form_data: dict,
    user=None,
    coupon_code: str | None = None,
) -> Order:
    """
    Crea la orden y sus items en la base de datos.
    No toca el carrito (se limpia recién al confirmar el pago).

    Args:
        cart: Instancia de Cart con los productos.
        form_data: Datos validados del CheckoutForm.
        user: Usuario logueado o None.
        coupon_code: Código de cupón aplicado (si hay).

    Returns:
        Order: La orden creada (ya commiteada en DB).
    """
    subtotal = cart.total_price

    # Calcular todos los descuentos y totales
    discounts = calculate_all_discounts(
        subtotal=subtotal,
        coupon_code=coupon_code,
        user=user,
    )

    # Crear la orden
    order = Order(
        user_id=user.id if user else None,
        customer_email=form_data["email"],
        customer_name=form_data["name"],
        customer_phone=form_data.get("phone"),
        shipping_address=form_data["address"],
        shipping_city=form_data["city"],
        shipping_state=form_data.get("state"),
        shipping_zip=form_data["zip_code"],
        shipping_country=form_data["country"],
        subtotal=subtotal,
        shipping_cost=discounts["shipping_cost"],
        total=discounts["final_total"],
        coupon_code=coupon_code,
        coupon_discount=discounts["coupon_discount"],
        level_discount=discounts["level_discount"],
        status=OrderStatus.PENDING_PAYMENT,
        notes=form_data.get("notes"),
    )
    db.session.add(order)
    db.session.flush()  # Obtener order.id sin commitear todavía

    # Crear los items
    for item in cart.items:
        product = item["product"]
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            quantity=item["quantity"],
            price=product.price,
        )
        db.session.add(order_item)

    db.session.commit()

    current_app.logger.info(
        f"✅ Orden #{order.id} creada. Total: ${order.total} "
        f"(cupón: -${order.coupon_discount}, nivel: -${order.level_discount})"
    )
    return order


def cleanup_failed_order(order: Order):
    """Elimina una orden que falló durante el proceso de pago."""
    try:
        db.session.delete(order)
        db.session.commit()
        current_app.logger.info(f"🗑️ Orden #{order.id} eliminada (pago fallido)")
    except Exception as e:
        current_app.logger.error(f"Error limpiando orden #{order.id}: {e}")
        db.session.rollback()