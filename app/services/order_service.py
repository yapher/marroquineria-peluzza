# app/services/order_service.py
"""
Lógica de confirmación de pago, centralizada para que la use tanto
el retorno del comprador (payment_return) como el webhook server-to-server
de Mercado Pago. Es idempotente: si la orden ya no está en pending_payment,
no hace nada (evita duplicar puntos/stock si MP reintenta la notificación
o si el usuario llega a confirmar por las dos vías).
"""
from flask import current_app
from ..extensions import db
from ..models import Product, Coupon, User
from ..config.constants import OrderStatus


def confirm_order_payment(order, payment_data: dict) -> bool:
    """
    Marca la orden como pagada, otorga puntos de fidelización, descuenta
    stock, incrementa el uso del cupón y envía el email de confirmación.

    Devuelve True si efectivamente confirmó el pago ahora, False si la
    orden ya estaba confirmada (para que el caller sepa si debe hacer
    tareas adicionales, como limpiar el carrito de la sesión).
    """
    if order.status != OrderStatus.PENDING_PAYMENT:
        current_app.logger.info(
            f"Orden #{order.id} ya estaba en estado '{order.status}', se ignora confirmación duplicada."
        )
        return False

    order.status = OrderStatus.PAID
    order.payment_method = "mercadopago"
    order.payment_status = payment_data.get("status", "approved")
    order.payment_id = str(payment_data.get("id", ""))

    # Puntos de fidelización
    if order.user_id:
        from .loyalty_service import award_points_for_order
        user = db.session.get(User, order.user_id)
        if user:
            award_points_for_order(order, user)

    # Reducir stock
    for item in order.items:
        product = db.session.get(Product, item.product_id)
        if product:
            product.stock -= item.quantity

    # Incrementar uso del cupón
    if order.coupon_code:
        coupon = Coupon.query.filter_by(code=order.coupon_code).first()
        if coupon:
            coupon.uses_count += 1

    db.session.commit()

    # Email de confirmación (best-effort, nunca rompe el flujo)
    try:
        from .email_service import send_order_confirmation
        send_order_confirmation(order)
    except Exception as e:
        current_app.logger.error(f"Error enviando email de confirmación (orden #{order.id}): {e}")

    current_app.logger.info(f"✅ Orden #{order.id} confirmada como pagada (payment_id={order.payment_id})")
    return True