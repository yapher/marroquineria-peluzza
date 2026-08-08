"""
Servicio de Mercado Pago (Checkout Pro).
Requiere MP_ACCESS_TOKEN en las variables de entorno.
"""
import os
import mercadopago
from flask import current_app, url_for


def get_sdk():
    token = os.getenv("MP_ACCESS_TOKEN")
    if not token:
        current_app.logger.error("❌ MP_ACCESS_TOKEN no está configurado")
        return None
    return mercadopago.SDK(token)


def create_preference(order):
    """
    Crea la preferencia de pago para una orden.
    Devuelve un dict con 'init_point' (URL de pago) o None si falla.
    """
    sdk = get_sdk()
    if not sdk:
        return None

    # Ítems del carrito
    items = []
    for item in order.items:
        items.append({
            "title": item.product_name,
            "description": f"SKU: {item.product_sku}",
            "quantity": int(item.quantity),
            "unit_price": float(item.price),
            "currency_id": "ARS",
        })

    # Envío
    if float(order.shipping_cost or 0) > 0:
        items.append({
            "title": "Envío",
            "quantity": 1,
            "unit_price": float(order.shipping_cost),
            "currency_id": "ARS",
        })

    # Descuentos (cupón + nivel de fidelización) como ítem negativo
    total_discount = float(order.coupon_discount or 0) + float(order.level_discount or 0)
    if total_discount > 0:
        label = f"Descuento {order.coupon_code}" if order.coupon_code else "Descuento fidelización"
        items.append({
            "title": label,
            "quantity": 1,
            "unit_price": -total_discount,
            "currency_id": "ARS",
        })

    preference_data = {
        "items": items,
        "payer": {
            "name": order.customer_name,
            "email": order.customer_email,
        },
        "back_urls": {
            "success": url_for("checkout.payment_return", order_id=order.id, _external=True),
            "pending": url_for("checkout.payment_return", order_id=order.id, _external=True),
            "failure": url_for("checkout.payment_failure", order_id=order.id, _external=True),
        },
        "external_reference": str(order.id),
        "statement_descriptor": "PELUZZA",  # aparece en el resumen de la tarjeta
        "payment_methods": {
            "installments": 12,  # hasta 12 cuotas
        },
    }

    # auto_return solo en producción (en localhost MP no puede redirigir)
    if not current_app.debug:
        preference_data["auto_return"] = "approved"

    try:
        response = sdk.preference().create(preference_data)
        if response.get("status") in (200, 201):
            pref = response["response"]
            current_app.logger.info(f"✅ Preferencia MP creada: {pref['id']}")
            return {
                "id": pref["id"],
                "init_point": pref["init_point"],
                "sandbox_init_point": pref.get("sandbox_init_point"),
            }
        current_app.logger.error(f"❌ Error creando preferencia MP: {response}")
        return None
    except Exception as e:
        current_app.logger.error(f"❌ Excepción creando preferencia MP: {e}")
        return None


def verify_payment(payment_id):
    """Consulta el estado REAL de un pago en la API de Mercado Pago."""
    sdk = get_sdk()
    if not sdk:
        return None
    try:
        response = sdk.payment().get(payment_id)
        if response.get("status") == 200:
            return response["response"]
        current_app.logger.error(f"❌ Error consultando pago: {response}")
        return None
    except Exception as e:
        current_app.logger.error(f"❌ Excepción consultando pago: {e}")
        return None