"""Rutas de estadísticas y reportes."""
from flask import render_template
from .. import admin_bp
from ....models import Order, OrderItem, Product, Category, User, Review
from ....extensions import db
from . import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func, extract


@admin_bp.route("/estadisticas")
@admin_required
def stats():
    """Panel de estadísticas con gráficos."""
    # Pedidos completados
    completed_orders = Order.query.filter(
        Order.status.in_(["paid", "shipped", "delivered", "completed"])
    ).all()
    
    total_revenue = sum(float(order.total) for order in completed_orders)
    total_orders = len(completed_orders)
    avg_ticket = total_revenue / total_orders if total_orders > 0 else 0
    
    pending_orders = Order.query.filter(Order.status == "pending_payment").count()
    cancelled_orders = Order.query.filter(Order.status == "cancelled").count()
    
    # Ventas mensuales (últimos 6 meses)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_data = (
        db.session.query(
            extract('year', Order.created_at).label('year'),
            extract('month', Order.created_at).label('month'),
            func.sum(Order.total).label('total_sales'),
            func.count(Order.id).label('order_count')
        )
        .filter(
            Order.status.in_(["paid", "shipped", "delivered", "completed"]),
            Order.created_at >= six_months_ago
        )
        .group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )
    
    months_labels = []
    monthly_revenue = []
    monthly_orders_count = []
    month_names = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
    
    for row in monthly_data:
        months_labels.append(f"{month_names.get(int(row.month), 'Mes')} {int(row.year)}")
        monthly_revenue.append(float(row.total_sales or 0))
        monthly_orders_count.append(int(row.order_count or 0))
    
    # Top productos
    top_products = (
        db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
        )
        .join(Order)
        .filter(Order.status.in_(["paid", "shipped", "delivered", "completed"]))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    
    # Ingresos por categoría
    revenue_by_category = (
        db.session.query(
            Category.name.label('category_name'),
            func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue'),
            func.sum(OrderItem.quantity).label('items_sold')
        )
        .join(Product, Product.id == OrderItem.product_id)
        .join(Category, Category.id == Product.category_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status.in_(["paid", "shipped", "delivered", "completed"]))
        .group_by(Category.name)
        .order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())
        .all()
    )
    
    category_labels = [row.category_name for row in revenue_by_category]
    category_revenue = [float(row.total_revenue or 0) for row in revenue_by_category]
    
    # Distribución de estados
    status_distribution = (
        db.session.query(Order.status, func.count(Order.id).label('count'))
        .group_by(Order.status)
        .all()
    )
    
    status_map = {
        "pending_payment": "Pago Pendiente", "pending": "Pendiente", "paid": "Pagado",
        "preparing": "En Preparación", "shipped": "Enviado", "delivered": "Entregado",
        "completed": "Completado", "cancelled": "Cancelado"
    }
    status_labels = [status_map.get(s, s) for s, _ in status_distribution]
    status_counts = [c for _, c in status_distribution]
    
    # Reseñas
    total_customers = User.query.filter_by(is_admin=False).count()
    total_reviews = Review.query.filter_by(approved=True).count()
    avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter(Review.approved == True)
        .scalar() or 0
    )
    
    return render_template(
        "admin/stats.html",
        total_revenue=total_revenue, total_orders=total_orders, avg_ticket=avg_ticket,
        pending_orders=pending_orders, cancelled_orders=cancelled_orders,
        months_labels=months_labels, monthly_revenue=monthly_revenue,
        monthly_orders_count=monthly_orders_count, top_products=top_products,
        category_labels=category_labels, category_revenue=category_revenue,
        status_labels=status_labels, status_counts=status_counts,
        total_customers=total_customers, total_reviews=total_reviews,
        avg_rating=round(float(avg_rating), 1),
    )