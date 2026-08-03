import os
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from slugify import slugify
from . import admin_bp
from ...extensions import db
from ...models import Product, Order, OrderItem, User, Category, Coupon, Review
from ...forms.admin_forms import ProductForm, CategoryForm
from ...forms.coupon_forms import CouponForm
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from decimal import Decimal


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Acceso restringido. Solo administradores.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "total_products": Product.query.count(),
        "total_orders": Order.query.count(),
        "total_customers": User.query.filter_by(is_admin=False).count(),
        "total_revenue": db.session.query(db.func.sum(Order.total)).scalar() or 0,
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, orders=recent_orders)


# ============================================
# PRODUCTOS
# ============================================

@admin_bp.route("/productos")
@admin_required
def products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=products)


@admin_bp.route("/productos/nuevo", methods=["GET", "POST"])
@admin_required
def product_new():
    form = ProductForm()
    if form.validate_on_submit():
        slug = form.slug.data or slugify(form.name.data)
        image_url = None

        file = request.files.get('image')
        if file and file.filename and file.filename != '':
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"

            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            save_path = os.path.join(upload_folder, unique_filename)
            file.save(save_path)

            image_url = f"/static/img/products/{unique_filename}"

        product = Product(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            short_description=form.short_description.data,
            price=form.price.data,
            compare_at_price=form.compare_at_price.data,
            stock=form.stock.data,
            sku=form.sku.data,
            artisan_name=form.artisan_name.data,
            category_id=form.category_id.data,
            is_handmade=form.is_handmade.data,
            featured=form.featured.data,
            active=form.active.data,
            image_url=image_url
        )
        db.session.add(product)
        db.session.commit()

        if image_url:
            flash(f"✅ Producto creado con imagen: {image_url}", "success")
        else:
            flash(f"✅ Producto '{product.name}' creado (sin imagen)", "success")
        return redirect(url_for("admin.products"))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en {field}: {error}", "error")

    return render_template("admin/product_form.html", form=form, title="Nuevo Producto")


@admin_bp.route("/productos/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        product.name = form.name.data
        product.slug = form.slug.data or slugify(form.name.data)
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.price = form.price.data
        product.compare_at_price = form.compare_at_price.data
        product.stock = form.stock.data
        product.sku = form.sku.data
        product.artisan_name = form.artisan_name.data
        product.category_id = form.category_id.data
        product.is_handmade = form.is_handmade.data
        product.featured = form.featured.data
        product.active = form.active.data

        file = request.files.get('image')
        if file and file.filename and file.filename != '':
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"

            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)

            save_path = os.path.join(upload_folder, unique_filename)
            file.save(save_path)

            product.image_url = f"/static/img/products/{unique_filename}"

        db.session.commit()
        flash(f"✅ Producto '{product.name}' actualizado", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", form=form, product=product, title="Editar Producto")


@admin_bp.route("/productos/<int:product_id>/eliminar", methods=["POST"])
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"✅ Producto '{product.name}' eliminado", "success")
    return redirect(url_for("admin.products"))


# ============================================
# CATEGORÍAS
# ============================================

@admin_bp.route("/categorias")
@admin_required
def categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=categories)


@admin_bp.route("/categorias/nueva", methods=["GET", "POST"])
@admin_required
def category_new():
    form = CategoryForm()
    if form.validate_on_submit():
        slug = form.slug.data or slugify(form.name.data)

        category = Category(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            active=form.active.data
        )
        db.session.add(category)
        db.session.commit()

        flash(f"✅ Categoría '{category.name}' creada", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/category_form.html", form=form, title="Nueva Categoría")


@admin_bp.route("/categorias/<int:category_id>/editar", methods=["GET", "POST"])
@admin_required
def category_edit(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data or slugify(form.name.data)
        category.description = form.description.data
        category.active = form.active.data

        db.session.commit()
        flash(f"✅ Categoría '{category.name}' actualizada", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/category_form.html", form=form, category=category, title="Editar Categoría")


# ============================================
# PEDIDOS
# ============================================

@admin_bp.route("/pedidos")
@admin_required
def orders():
    # Filtros opcionales
    status_filter = request.args.get("status")
    
    query = Order.query
    
    if status_filter and status_filter != "all":
        query = query.filter_by(status=status_filter)
    
    orders_list = query.order_by(Order.created_at.desc()).all()
    
    # Contadores por estado
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
    
    return render_template("admin/orders.html", 
                         orders=orders_list, 
                         stats=stats,
                         current_status=status_filter or "all")


@admin_bp.route("/pedidos/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order)


@admin_bp.route("/pedidos/<int:order_id>/cambiar-estado", methods=["POST"])
@admin_required
def order_change_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    new_status = request.form.get("status")
    tracking_number = request.form.get("tracking_number", "").strip()
    notes = request.form.get("admin_notes", "").strip()
    
    # Validar que el nuevo estado sea válido
    if new_status not in order.next_statuses:
        flash(f"❌ No se puede cambiar de '{order.status_display}' a '{new_status}'", "error")
        return redirect(url_for("admin.order_detail", order_id=order.id))
    
    old_status = order.status
    order.status = new_status
    
    # Guardar número de tracking si se envió
    if tracking_number and new_status == "shipped":
        order.tracking_number = tracking_number
    
    # Guardar notas del admin
    if notes:
        if order.admin_notes:
            order.admin_notes += f"\n\n[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}]\n{notes}"
        else:
            order.admin_notes = f"[{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}]\n{notes}"
    
    db.session.commit()
    
    # Enviar email de notificación al cliente
    try:
        from ...services.email_service import send_order_status_update
        send_order_status_update(order, old_status, new_status)
        flash(f"✅ Estado actualizado y email enviado a {order.customer_email}", "success")
    except Exception as e:
        current_app.logger.error(f"Error enviando email: {e}")
        flash(f"✅ Estado actualizado (pero no se pudo enviar el email)", "warning")
    
    return redirect(url_for("admin.order_detail", order_id=order.id))


# ============================================
# CUPONES
# ============================================

@admin_bp.route("/cupones")
@admin_required
def coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template("admin/coupons.html", coupons=coupons)


@admin_bp.route("/cupones/nuevo", methods=["GET", "POST"])
@admin_required
def coupon_new():
    form = CouponForm()
    if form.validate_on_submit():
        if Coupon.query.filter_by(code=form.code.data.upper()).first():
            flash(f"❌ El código '{form.code.data}' ya existe", "error")
            return render_template("admin/coupon_form.html", form=form, title="Nuevo Cupón")
        
        coupon = Coupon(
            code=form.code.data.upper(),
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_purchase=form.min_purchase.data or 0,
            max_uses=form.max_uses.data or 0,
            valid_until=form.valid_until.data,
            description=form.description.data,
            active=form.active.data
        )
        db.session.add(coupon)
        db.session.commit()
        
        flash(f"✅ Cupón '{coupon.code}' creado exitosamente", "success")
        return redirect(url_for("admin.coupons"))
    
    return render_template("admin/coupon_form.html", form=form, title="Nuevo Cupón")


@admin_bp.route("/cupones/<int:coupon_id>/editar", methods=["GET", "POST"])
@admin_required
def coupon_edit(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    form = CouponForm(obj=coupon)
    
    if form.validate_on_submit():
        existing = Coupon.query.filter_by(code=form.code.data.upper()).first()
        if existing and existing.id != coupon.id:
            flash(f"❌ El código '{form.code.data}' ya existe", "error")
            return render_template("admin/coupon_form.html", form=form, coupon=coupon, title="Editar Cupón")
        
        coupon.code = form.code.data.upper()
        coupon.discount_type = form.discount_type.data
        coupon.discount_value = form.discount_value.data
        coupon.min_purchase = form.min_purchase.data or 0
        coupon.max_uses = form.max_uses.data or 0
        coupon.valid_until = form.valid_until.data
        coupon.description = form.description.data
        coupon.active = form.active.data
        
        db.session.commit()
        flash(f"✅ Cupón '{coupon.code}' actualizado", "success")
        return redirect(url_for("admin.coupons"))
    
    return render_template("admin/coupon_form.html", form=form, coupon=coupon, title="Editar Cupón")


@admin_bp.route("/cupones/<int:coupon_id>/eliminar", methods=["POST"])
@admin_required
def coupon_delete(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    flash(f"✅ Cupón '{coupon.code}' eliminado", "success")
    return redirect(url_for("admin.coupons"))


# ============================================
# DASHBOARD DE ESTADÍSTICAS
# ============================================

@admin_bp.route("/estadisticas")
@admin_required
def stats():
    """Dashboard avanzado de estadísticas."""
    
    # ==========================================
    # MÉTRICAS GENERALES
    # ==========================================
    
    # Total de pedidos pagados o completados
    completed_orders = Order.query.filter(
        Order.status.in_(["paid", "shipped", "delivered", "completed"])
    ).all()
    
    total_revenue = sum(float(order.total) for order in completed_orders)
    total_orders = len(completed_orders)
    avg_ticket = total_revenue / total_orders if total_orders > 0 else 0
    
    # Pedidos pendientes de pago
    pending_orders = Order.query.filter(
        Order.status == "pending_payment"
    ).count()
    
    # Pedidos cancelados
    cancelled_orders = Order.query.filter(
        Order.status == "cancelled"
    ).count()
    
    # ==========================================
    # VENTAS POR MES (Últimos 6 meses)
    # ==========================================
    
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Agrupar por año y mes
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
    
    # Preparar datos para Chart.js
    months_labels = []
    monthly_revenue = []
    monthly_orders_count = []
    
    month_names = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }
    
    for row in monthly_data:
        months_labels.append(f"{month_names.get(int(row.month), 'Mes')} {int(row.year)}")
        monthly_revenue.append(float(row.total_sales or 0))
        monthly_orders_count.append(int(row.order_count or 0))
    
    # ==========================================
    # TOP 5 PRODUCTOS MÁS VENDIDOS
    # ==========================================
    
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
    
    # ==========================================
    # INGRESOS POR CATEGORÍA
    # ==========================================
    
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
    
    # Preparar datos para gráfico de categorías
    category_labels = [row.category_name for row in revenue_by_category]
    category_revenue = [float(row.total_revenue or 0) for row in revenue_by_category]
    
    # ==========================================
    # DISTRIBUCIÓN DE ESTADOS
    # ==========================================
    
    status_distribution = (
        db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        )
        .group_by(Order.status)
        .all()
    )
    
    # Convertir a diccionario
    status_map = {
        "pending_payment": "Pago Pendiente",
        "pending": "Pendiente",
        "paid": "Pagado",
        "preparing": "En Preparación",
        "shipped": "Enviado",
        "delivered": "Entregado",
        "completed": "Completado",
        "cancelled": "Cancelado"
    }
    
    status_labels = []
    status_counts = []
    for status, count in status_distribution:
        status_labels.append(status_map.get(status, status))
        status_counts.append(count)
    
    # ==========================================
    # CLIENTES Y RESEÑAS
    # ==========================================
    
    total_customers = User.query.filter_by(is_admin=False).count()
    total_reviews = Review.query.filter_by(approved=True).count()
    avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter(Review.approved == True)
        .scalar() or 0
    )
    
    return render_template(
        "admin/stats.html",
        # Métricas generales
        total_revenue=total_revenue,
        total_orders=total_orders,
        avg_ticket=avg_ticket,
        pending_orders=pending_orders,
        cancelled_orders=cancelled_orders,
        # Gráficos
        months_labels=months_labels,
        monthly_revenue=monthly_revenue,
        monthly_orders_count=monthly_orders_count,
        # Productos
        top_products=top_products,
        # Categorías
        category_labels=category_labels,
        category_revenue=category_revenue,
        # Estados
        status_labels=status_labels,
        status_counts=status_counts,
        # Clientes y reseñas
        total_customers=total_customers,
        total_reviews=total_reviews,
        avg_rating=round(float(avg_rating), 1),
    )

# ============================================
# MODERACIÓN DE RESEÑAS
# ============================================

@admin_bp.route("/reseñas")
@admin_required
def reviews():
    """Lista todas las reseñas con filtros."""
    from ...models import Review
    
    # Filtros
    status_filter = request.args.get("status", "pending")
    
    query = Review.query.join(User).join(Product)
    
    if status_filter == "pending":
        query = query.filter(Review.approved == False)
    elif status_filter == "approved":
        query = query.filter(Review.approved == True)
    
    reviews_list = query.order_by(Review.created_at.desc()).all()
    
    # Contadores
    stats = {
        "total": Review.query.count(),
        "pending": Review.query.filter_by(approved=False).count(),
        "approved": Review.query.filter_by(approved=True).count(),
    }
    
    return render_template("admin/reviews.html", 
                         reviews=reviews_list, 
                         stats=stats,
                         current_status=status_filter)


@admin_bp.route("/reseñas/<int:review_id>/aprobar", methods=["POST"])
@admin_required
def approve_review(review_id):
    """Aprueba una reseña."""
    from ...models import Review
    
    review = Review.query.get_or_404(review_id)
    review.approved = True
    db.session.commit()
    
    # Enviar notificación al usuario (opcional)
    try:
        from ...services.email_service import send_review_approved
        send_review_approved(review)
    except Exception as e:
        current_app.logger.error(f"Error enviando email de aprobación: {e}")
    
    flash(f"✅ Reseña de {review.user.first_name} aprobada", "success")
    return redirect(url_for("admin.reviews", status=request.args.get("status", "pending")))


@admin_bp.route("/reseñas/<int:review_id>/rechazar", methods=["POST"])
@admin_required
def reject_review(review_id):
    """Rechaza y elimina una reseña."""
    from ...models import Review
    
    review = Review.query.get_or_404(review_id)
    user_name = review.user.first_name
    product_name = review.product.name
    
    db.session.delete(review)
    db.session.commit()
    
    flash(f"❌ Reseña de {user_name} para {product_name} rechazada y eliminada", "warning")
    return redirect(url_for("admin.reviews", status=request.args.get("status", "pending")))