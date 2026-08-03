import stripe
from flask import current_app, url_for
from decimal import Decimal


def init_stripe():
    """Inicializa Stripe con la clave secreta."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']


def create_checkout_session(order, success_url=None, cancel_url=None):
    """
    Crea una sesión de checkout de Stripe.
    
    Args:
        order: Objeto Order con los datos del pedido
        success_url: URL de retorno después del pago exitoso
        cancel_url: URL de retorno si el cliente cancela
    
    Returns:
        URL de la sesión de checkout
    """
    init_stripe()
    
    if not success_url:
        success_url = url_for('checkout.payment_success', order_id=order.id, _external=True)
    if not cancel_url:
        cancel_url = url_for('checkout.payment_cancel', _external=True)
    
    # Convertir productos a formato Stripe
    line_items = []
    for item in order.items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item.product_name,
                    'description': f'SKU: {item.product_sku}',
                },
                'unit_amount': int(item.price * 100),  # Stripe usa centavos
            },
            'quantity': item.quantity,
        })
    
    # Agregar costo de envío si existe
    if order.shipping_cost > 0:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Envío',
                },
                'unit_amount': int(order.shipping_cost * 100),
            },
            'quantity': 1,
        })
    
    # Aplicar descuento si hay cupón
    if order.coupon_discount > 0:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Descuento ({order.coupon_code})',
                },
                'unit_amount': -int(order.coupon_discount * 100),  # Negativo = descuento
            },
            'quantity': 1,
        })
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=order.customer_email,
            metadata={
                'order_id': str(order.id),
            },
        )
        return checkout_session.url
    except Exception as e:
        current_app.logger.error(f"Error creando sesión de Stripe: {e}")
        return None


def verify_webhook_signature(payload, sig_header):
    """
    Verifica la firma del webhook de Stripe.
    
    Returns:
        Evento verificado o None si la firma es inválida
    """
    init_stripe()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
        return event
    except ValueError:
        current_app.logger.error("Error parsing payload de Stripe")
        return None
    except stripe.error.SignatureVerificationError:
        current_app.logger.error("Firma de webhook inválida")
        return None