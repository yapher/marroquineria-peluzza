"""Rutas para gestión de pedidos."""
from flask import render_template, request, flash, redirect, url_for, Response
from .. import admin_bp
from ....models import Order, Product, User, Coupon
from ....extensions import db
from ....services.loyalty_service import award_points_for_order
from ....services.email_service import send_order_status_update
from . import admin_required
from datetime import datetime
import csv
import io


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
    stats = {
        "total": Order.query.count(),
        "pending_payment": Order.query.filter_by(status="pending_payment").count(),
        "paid": Order.query.filter_by(status="paid").count(),
        "preparing": Order.query.filter_by(status="preparing").count(),
        "shipped": Order.query.filter_by(status="shipped").count(),
        "delivered": Order.query.filter_by(status="delivered").count(),
        "completed": Order.query.filter_by(status="completed").count(),
        "cancelled": Order.query.filter_by(status="cancelled").count(),
    }
    return render_template("admin/orders.html", orders=orders_list, stats=stats, current_status=status_filter or "all")


@admin_bp.route("/pedidos/<int:order_id>")
@admin_required
def order_detail(order_id):
    """Muestra el detalle de un pedido."""
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order)


# ============================================
# CAMBIO DE ESTADO
# ============================================

@admin_bp.route("/pedidos/<int:order_id>/cambiar-estado", methods=["POST"])
@admin_required
def order_change_status(order_id):
    """Cambia el estado de un pedido y notifica al cliente."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    tracking_number = request.form.get("tracking_number", "").strip()
    notes = request.form.get("admin_notes", "").strip()
    
    if new_status not in order.next_statuses:
        flash(f"❌ No se puede cambiar de '{order.status_display}' a '{new_status}'", "error")
        return redirect(url_for("admin.order_detail", order_id=order.id))
    
    old_status = order.status
    order.status = new_status
    
    if tracking_number and new_status == "shipped":
        order.tracking_number = tracking_number
    
    if notes:
        if order.admin_notes:
            order.admin_notes += f"\n[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] {notes}"
        else:
            order.admin_notes = f"[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] {notes}"
    
    # Lógica de negocio según el estado
    if new_status == "paid" and old_status in ("pending_payment", "pending"):
        if order.user_id:
            user = User.query.get(order.user_id)
            if user:
                award_points_for_order(order, user)
        
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock -= item.quantity
        
        if order.coupon_code:
            coupon = Coupon.query.filter_by(code=order.coupon_code).first()
            if coupon:
                coupon.uses_count += 1
    
    if new_status == "cancelled" and old_status in ("paid", "preparing", "shipped"):
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
    
    db.session.commit()
    
    # Notificar al cliente
    try:
        send_order_status_update(order, old_status, new_status)
        flash(f"✅ Estado actualizado y email enviado a {order.customer_email}", "success")
    except Exception as e:
        from flask import current_app
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
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Crear el archivo CSV en memoria
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Encabezados
    cw.writerow([
        "ID Pedido", "Fecha", "Cliente", "Email", "Teléfono",
        "Estado", "Total", "Método de Pago", "Dirección", "Ciudad", "Código Postal"
    ])
    
    # Filas de datos
    for order in orders:
        nombre = getattr(order, 'customer_name', f"{getattr(order, 'first_name', '')} {getattr(order, 'last_name', '')}".strip())
        fecha = order.created_at.strftime("%d/%m/%Y %H:%M") if order.created_at else ""
        
        cw.writerow([
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
        ])
    
    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=pedidos.csv"}
    )