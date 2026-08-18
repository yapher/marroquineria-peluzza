# app/services/loyalty_service.py
"""
Servicio de fidelización: otorga puntos por compras completadas.

⚠️ El cálculo de descuentos por nivel vive en discount_calculator
(única fuente de verdad). Este módulo solo otorga puntos.
"""
from decimal import Decimal

from flask import flash

from ..config.constants import POINTS_PER_DOLLAR


def calculate_points_from_order(order) -> int:
    """
    Calcula los puntos a otorgar por una orden.
    Regla: 1 punto por cada $10 gastados.
    """
    # Usar el total de la orden (incluye envío, excluye descuentos)
    total = float(order.total)
    points = int(total // POINTS_PER_DOLLAR)
    return points


def award_points_for_order(order, user):
    """
    Otorga puntos al usuario por una compra completada.
    Se llama cuando el pedido cambia a estado 'paid' o superior.
    """
    if not user:
        return

    # Calcular puntos
    points = calculate_points_from_order(order)
    if points <= 0:
        return

    # Agregar puntos
    leveled_up = user.add_points(
        points=points,
        reason=f"Compra #{order.id} - ${order.total}",
        order_id=order.id
    )

    # Actualizar total gastado
    user.total_spent = (user.total_spent or Decimal("0")) + order.total

    # Mensaje flash
    if leveled_up:
        flash(f"🎉 ¡Ganaste {points} puntos y subiste a {user.loyalty_level_display}!", "success")
    else:
        flash(f"⭐ Ganaste {points} puntos por tu compra", "info")