# app/services/discount_calculator.py
"""
Calculadora de descuentos y costos de envío centralizada.

Separa la lógica de cupones, niveles de fidelización y costo de envío
para que pueda reutilizarse en checkout, resumen de carrito, etc.
"""
from decimal import Decimal

from ..models import Coupon
from ..config.constants import DEFAULT_SHIPPING_COST, FREE_SHIPPING_THRESHOLD


def calculate_coupon_discount(subtotal: Decimal, coupon_code: str | None) -> Decimal:
    """
    Calcula el descuento de un cupón sobre el subtotal.
    Devuelve Decimal("0") si el cupón no es válido o no existe.
    """
    if not coupon_code:
        return Decimal("0")

    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if not coupon or not coupon.is_valid:
        return Decimal("0")

    if subtotal < coupon.min_purchase:
        return Decimal("0")

    return coupon.apply_discount(subtotal)


def calculate_level_discount(subtotal_after_coupon: Decimal, user) -> Decimal:
    """
    Calcula el descuento por nivel de fidelización.
    Se aplica sobre el subtotal DESPUÉS del cupón.
    Devuelve Decimal("0") si el usuario no tiene descuento por nivel.
    """
    if user is None or not hasattr(user, 'loyalty_discount'):
        return Decimal("0")

    discount_percent = user.loyalty_discount
    if discount_percent <= 0:
        return Decimal("0")

    return subtotal_after_coupon * Decimal(discount_percent) / Decimal("100")


def calculate_shipping_cost(subtotal: Decimal) -> Decimal:
    """
    Calcula el costo de envío según el subtotal.

    Regla de negocio: envío GRATIS cuando el subtotal alcanza o supera
    FREE_SHIPPING_THRESHOLD ($100). En caso contrario se cobra el envío
    estándar (DEFAULT_SHIPPING_COST).

    ⚠️ Esta regla ya estaba prometida en la web (index y /envios) pero
    el código no la aplicaba: siempre se cobraba el envío fijo.
    """
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return Decimal("0")
    return DEFAULT_SHIPPING_COST


def calculate_all_discounts(
    subtotal: Decimal,
    coupon_code: str | None = None,
    user=None
) -> dict:
    """
    Calcula todos los descuentos y el envío de una vez.
    Devuelve un dict con:
    - coupon_discount: Decimal
    - level_discount: Decimal
    - total_discount: Decimal
    - shipping_cost: Decimal
    - final_total: Decimal
    """
    coupon_discount = calculate_coupon_discount(subtotal, coupon_code)
    base_for_level = subtotal - coupon_discount
    level_discount = calculate_level_discount(base_for_level, user)
    shipping_cost = calculate_shipping_cost(subtotal)

    total_discount = coupon_discount + level_discount
    final_total = subtotal + shipping_cost - total_discount

    return {
        "coupon_discount": coupon_discount,
        "level_discount": level_discount,
        "total_discount": total_discount,
        "shipping_cost": shipping_cost,
        "final_total": final_total,
    }


def validate_coupon(coupon_code: str, subtotal: Decimal) -> tuple[bool, str]:
    """
    Valida un cupón y devuelve (es_valido, mensaje_error).
    Útil para el endpoint /aplicar-cupon.
    """
    if not coupon_code:
        return False, "Ingresa un código de cupón"

    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if not coupon:
        return False, "❌ Cupón no encontrado"

    if not coupon.is_valid:
        return False, "❌ Este cupón ya no es válido"

    if subtotal < coupon.min_purchase:
        return False, f"❌ Compra mínima requerida: ${coupon.min_purchase}"

    return True, ""