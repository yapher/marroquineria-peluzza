"""Rutas del dashboard principal del admin."""
from flask import render_template
from .. import admin_bp
from ....models import Product, Order, User
from ....extensions import db
from . import admin_required


@admin_bp.route("/")
@admin_required
def dashboard():
    """Panel principal con estadísticas rápidas."""
    stats = {
        "total_products": Product.query.count(),
        "total_orders": Order.query.count(),
        "total_customers": User.query.filter_by(is_admin=False).count(),
        "total_revenue": db.session.query(db.func.sum(Order.total)).scalar() or 0,
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, orders=recent_orders)