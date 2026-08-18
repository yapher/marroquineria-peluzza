# app/blueprints/admin/routes/orders.py
"""Rutas para gestión de pedidos."""
from flask import render_template, request, flash, redirect, url_for, Response, current_app, abort 

from .. import admin_bp
from ....models import Order, OrderItem, Product, User, Coupon, LoyaltyTransaction
from ....extensions import db
from ....services.loyalty_service import award_points_for_order
from ....services.email_service import send_order_status_update
from ....config.constants import OrderStatus, ORDER_STATUS_META
from ....utils.time import utc_now
from ....utils.csv_export import orders_to_csv
from . import admin_required


# ============================================
# LISTADO Y DETALLE
# ============================================
@admin_bp.route("/pedidos")
@admin_required
def orders():
    """Lista todos los pedidos con filtros."""
    status_filter = request.args.get("status")

    query = Order.query
    if status_filter and status_filter != "all":
        query = query.filter_by(status=status_filter)

    orders_list = query.order_by(Order.created_at.desc()).all()

    stats = {"total": Order.query.count()}
    for status_key in ORDER_STATUS_META:
        stats[status_key] = Order.query.filter_by(status=status_key).count()

    return render_template(
        "admin/orders.html",
        orders=orders_list,
        stats=stats,
        current_status=status_filter or "all"
    )

# ============================================
# BORRAR TODOS LOS PEDIDOS (limpieza)
# ============================================
@admin_bp.route("/pedidos/borrar-todos", methods=["POST"])
@admin_required
def orders_delete_all():
    """
    Elimina TODOS los pedidos y sus dependencias para permitir
    borrar los productos después.

    Orden de borrado (respeta las Foreign Keys):
      1. LoyaltyTransaction (order_id -> orders.id)
      2. OrderItem         (order_id -> orders.id, product_id -> products.id)
      3. Order
    """
    # 1. Transacciones de fidelización ligadas a pedidos
    LoyaltyTransaction.query.filter(
        LoyaltyTransaction.order_id.isnot(None)
    ).delete(synchronize_session=False)

    # 2. Items de pedido (son los que bloquean el borrado de productos)
    OrderItem.query.delete(synchronize_session=False)

    # 3. Pedidos
    orders_count = Order.query.delete(synchronize_session=False)

    db.session.commit()
    flash(f"✅ Se eliminaron {orders_count} pedidos y sus items asociados", "success")
    return redirect(url_for("admin.orders"))



@admin_bp.route("/pedidos/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    return render_template("admin/order_detail.html", order=order)


# ============================================
# CAMBIO DE ESTADO
# ============================================
@admin_bp.route("/pedidos/<int:order_id>/cambiar-estado", methods=["POST"])
@admin_required
def order_change_status(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    
    new_status = request.form.get("status")
    tracking_number = request.form.get("tracking_number", "").strip()
    notes = request.form.get("admin_notes", "").strip()

    if new_status not in order.next_statuses:
        flash(f"❌ No se puede cambiar de '{order.status_display}' a '{new_status}'", "error")
        return redirect(url_for("admin.order_detail", order_id=order.id))

    old_status = order.status
    order.status = new_status

    if tracking_number and new_status == OrderStatus.SHIPPED:
        order.tracking_number = tracking_number

    if notes:
        now_str = utc_now().strftime('%d/%m/%Y %H:%M')
        if order.admin_notes:
            order.admin_notes += f"\n[{now_str}] {notes}"
        else:
            order.admin_notes = f"[{now_str}] {notes}"

    # Lógica de negocio según el estado
    if new_status == OrderStatus.PAID and old_status in (OrderStatus.PENDING_PAYMENT, OrderStatus.PENDING):
        if order.user_id:
            user = db.session.get(User, order.user_id)
            if user:
                award_points_for_order(order, user)

        for item in order.items:
            product = db.session.get(Product, item.product_id)
            if product:
                product.stock -= item.quantity

        if order.coupon_code:
            coupon = Coupon.query.filter_by(code=order.coupon_code).first()
            if coupon:
                coupon.uses_count += 1

    if new_status == OrderStatus.CANCELLED and old_status in (OrderStatus.PAID, OrderStatus.PREPARING, OrderStatus.SHIPPED):
        for item in order.items:
            product = db.session.get(Product, item.product_id)
            if product:
                product.stock += item.quantity

    db.session.commit()

    # Notificar al cliente
    try:
        send_order_status_update(order, old_status, new_status)
        flash(f"✅ Estado actualizado y email enviado a {order.customer_email}", "success")
    except Exception as e:
        current_app.logger.error(f"Error enviando email: {e}")
        flash("✅ Estado actualizado (pero no se pudo enviar el email)", "warning")

    return redirect(url_for("admin.order_detail", order_id=order.id))


# ============================================
# EXPORTAR A CSV
# ============================================
@admin_bp.route("/pedidos/exportar-csv")
@admin_required
def export_orders_csv():
    """Exporta los pedidos a un archivo CSV compatible con Excel."""
    status_filter = request.args.get("status")

    query = Order.query
    if status_filter and status_filter != "all":
        query = query.filter_by(status=status_filter)

    orders_list = query.order_by(Order.created_at.desc()).all()
    output = orders_to_csv(orders_list)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=pedidos.csv"}
    )