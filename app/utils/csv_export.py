# app/utils/csv_export.py
"""
Generación de reportes CSV.

Extraído de admin/routes/orders.py para mantener las rutas declarativas
y hacer la lógica de exportación testeable y reutilizable.
"""
import csv
import io


# Encabezados del CSV de pedidos (compatible con Excel)
ORDER_CSV_HEADERS = [
    "ID Pedido", "Fecha", "Cliente", "Email", "Teléfono",
    "Estado", "Total", "Método de Pago", "Dirección", "Ciudad", "Código Postal"
]


def _order_to_row(order) -> list:
    """Convierte una orden en una fila del CSV."""
    nombre = getattr(
        order, 'customer_name',
        f"{getattr(order, 'first_name', '')} {getattr(order, 'last_name', '')}".strip()
    )
    fecha = order.created_at.strftime("%d/%m/%Y %H:%M") if order.created_at else ""

    return [
        order.id,
        fecha,
        nombre,
        getattr(order, 'customer_email', ''),
        getattr(order, 'customer_phone', ''),
        order.status,
        f"${order.total:.2f}" if order.total else "$0.00",
        getattr(order, 'payment_method', 'N/A'),
        getattr(order, 'shipping_address', ''),
        getattr(order, 'shipping_city', ''),
        getattr(order, 'shipping_zip', getattr(order, 'shipping_zip_code', ''))
    ]


def orders_to_csv(orders) -> str:
    """
    Genera el contenido CSV de una lista de pedidos.

    Args:
        orders: Lista de objetos Order.

    Returns:
        str: Contenido CSV completo (encabezados + filas).
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(ORDER_CSV_HEADERS)

    for order in orders:
        writer.writerow(_order_to_row(order))

    output = buffer.getvalue()
    buffer.close()
    return output