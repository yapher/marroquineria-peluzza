# app/config/constants.py
"""
Constantes centralizadas del dominio.

⚠️  REGLA DE ORO:
Los valores de texto (estados de pedido y niveles de fidelización)
están guardados en la base de datos. NO cambiarlos jamás.
Este módulo solo centraliza esos valores para no tenerlos repetidos
en modelos, servicios, rutas y templates.
"""
from decimal import Decimal


# ============================================
# ESTADOS DE PEDIDO
# ============================================

class OrderStatus:
    """Estados posibles de un pedido (valores persistidos en DB)."""
    PENDING_PAYMENT = "pending_payment"
    PENDING         = "pending"
    PAID            = "paid"
    PREPARING       = "preparing"
    SHIPPED         = "shipped"
    DELIVERED       = "delivered"
    COMPLETED       = "completed"
    CANCELLED       = "cancelled"


# Metadatos de presentación de cada estado (labels, iconos, colores para la UI)
ORDER_STATUS_META = {
    OrderStatus.PENDING_PAYMENT: {"label": "Pago Pendiente", "icon": "💳", "color": "yellow"},
    OrderStatus.PENDING:         {"label": "Pendiente",       "icon": "⏳", "color": "yellow"},
    OrderStatus.PAID:            {"label": "Pagado",          "icon": "✅", "color": "blue"},
    OrderStatus.PREPARING:       {"label": "En Preparación",  "icon": "📦", "color": "purple"},
    OrderStatus.SHIPPED:         {"label": "Enviado",         "icon": "🚚", "color": "indigo"},
    OrderStatus.DELIVERED:       {"label": "Entregado",       "icon": "🏠", "color": "green"},
    OrderStatus.COMPLETED:       {"label": "Completado",      "icon": "🎉", "color": "green"},
    OrderStatus.CANCELLED:       {"label": "Cancelado",       "icon": "❌", "color": "red"},
}

# Flujo de transiciones permitidas: estado_actual -> [estados posibles]
ORDER_FLOW = {
    OrderStatus.PENDING_PAYMENT: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PENDING:         [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID:            [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING:       [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED:         [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED:       [OrderStatus.COMPLETED],
    OrderStatus.COMPLETED:       [],
    OrderStatus.CANCELLED:       [],
}

# Estados que cuentan como "venta concretada" (ingresos, estadísticas)
COMPLETED_ORDER_STATUSES = [
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
    OrderStatus.COMPLETED,
]

# Estados que habilitan al cliente a reseñar un producto comprado
REVIEWABLE_ORDER_STATUSES = COMPLETED_ORDER_STATUSES


def get_order_status_meta(status: str) -> dict:
    """Metadatos de un estado, con fallback seguro para estados desconocidos."""
    return ORDER_STATUS_META.get(status, {"label": status, "icon": "📋", "color": "gray"})


# ============================================
# SISTEMA DE FIDELIZACIÓN
# ============================================

class LoyaltyLevel:
    """Niveles de fidelización (valores persistidos en DB)."""
    BRONZE   = "bronze"
    SILVER   = "silver"
    GOLD     = "gold"
    PLATINUM = "platinum"


# Definición de cada nivel: umbral de puntos, descuento % y nombre para mostrar
LOYALTY_LEVELS = {
    LoyaltyLevel.BRONZE:   {"name": "Bronce 🥉",   "threshold": 0,     "discount": 0},
    LoyaltyLevel.SILVER:   {"name": "Plata 🥈",    "threshold": 1000,  "discount": 5},
    LoyaltyLevel.GOLD:     {"name": "Oro 🥇",      "threshold": 5000,  "discount": 10},
    LoyaltyLevel.PLATINUM: {"name": "Platino 💎",  "threshold": 10000, "discount": 15},
}

# Niveles que otorgan descuento automático en el checkout
LOYALTY_LEVELS_WITH_DISCOUNT = [
    LoyaltyLevel.SILVER,
    LoyaltyLevel.GOLD,
    LoyaltyLevel.PLATINUM,
]

# Puntos ganados por cada $10 de compra
POINTS_PER_DOLLAR = 10


def get_next_loyalty_level(current_level: str) -> dict:
    """Información del siguiente nivel (o 'Máximo' si ya es Platino)."""
    order = [LoyaltyLevel.BRONZE, LoyaltyLevel.SILVER, LoyaltyLevel.GOLD, LoyaltyLevel.PLATINUM]
    idx = order.index(current_level) if current_level in order else 0

    if idx >= len(order) - 1:
        return {
            "name": "Máximo",
            "points": None,
            "discount": LOYALTY_LEVELS[LoyaltyLevel.PLATINUM]["discount"],
        }

    next_key = order[idx + 1]
    return {
        "name": LOYALTY_LEVELS[next_key]["name"],
        "points": LOYALTY_LEVELS[next_key]["threshold"],
        "discount": LOYALTY_LEVELS[next_key]["discount"],
    }


# ============================================
# CARRITO / CHECKOUT
# ============================================

DEFAULT_SHIPPING_COST = Decimal("10.00")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")