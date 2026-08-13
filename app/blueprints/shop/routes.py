# app/blueprints/shop/routes.py
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from . import shop_bp
from ...models import Product, Category, Review, Order, OrderItem
from ...extensions import db, csrf
from ...config.constants import REVIEWABLE_ORDER_STATUSES


# ============================================
# CATÁLOGO
# ============================================

@shop_bp.route("/")
def catalog():
    # Parámetros de la URL
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("categoria")
    sort = request.args.get("sort", "recent")
    search = request.args.get("q", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    # Query base
    query = Product.query.filter_by(active=True)

    # Filtro por categoría
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)

    # Filtro por búsqueda
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.artisan_name.ilike(f"%{search}%")
            )
        )

    # Filtro por precio
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Ordenamiento
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "name":
        query = query.order_by(Product.name.asc())
    else:  # recent
        query = query.order_by(Product.created_at.desc())

    # Paginación
    pagination = query.paginate(page=page, per_page=12, error_out=False)

    # Categorías para el sidebar
    categories = Category.query.filter_by(active=True).all()

    # Si es HTMX, devolvemos solo la grilla de productos
    if request.headers.get('HX-Request'):
        return render_template(
            "shop/partials/product_grid.html",
            products=pagination.items,
            pagination=pagination,
        )

    # Si es petición normal, devolvemos la página completa
    return render_template(
        "shop/catalog.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=category_slug,
        current_sort=sort,
        search=search,
        min_price=min_price,
        max_price=max_price,
    )


# ============================================
# DETALLE DE PRODUCTO
# ============================================

@shop_bp.route("/producto/<slug>")
def product_detail(slug: str):
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()

    # Productos relacionados: misma categoría
    related = (
        Product.query
        .filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.active == True
        )
        .order_by(func.random())
        .limit(4)
        .all()
    )

    # Si no hay suficientes, buscar del mismo artesano
    if len(related) < 4 and product.artisan_name:
        extra = (
            Product.query
            .filter(
                Product.artisan_name == product.artisan_name,
                Product.id != product.id,
                Product.active == True,
                ~Product.id.in_([p.id for p in related])
            )
            .order_by(func.random())
            .limit(4 - len(related))
            .all()
        )
        related.extend(extra)

    return render_template("shop/product.html", product=product, related=related)


# ============================================
# BÚSQUEDA EN TIEMPO REAL (HTMX)
# ============================================

@shop_bp.route("/buscar")
def search_ajax():
    """Devuelve resultados de búsqueda en tiempo real para HTMX."""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return ""

    products = Product.query.filter(
        Product.active == True,
        Product.name.ilike(f"%{query}%")
    ).limit(5).all()

    return render_template(
        "shop/partials/search_dropdown.html",
        products=products,
        query=query
    )


# ============================================
# RESEÑAS
# ============================================

@shop_bp.route("/producto/<slug>/reseña", methods=["POST"])
@login_required
def add_review(slug: str):
    """Agrega una reseña a un producto."""
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()

    # Validar que el usuario compró este producto
    purchased = OrderItem.query.join(Order).filter(
        Order.user_id == current_user.id,
        Order.status.in_(REVIEWABLE_ORDER_STATUSES),
        OrderItem.product_id == product.id
    ).first()

    if not purchased:
        flash("❌ Solo puedes reseñar productos que hayas comprado", "error")
        return redirect(url_for("shop.product_detail", slug=slug))

    # Validar que no haya reseñado antes
    if product.has_user_reviewed(current_user.id):
        flash("❌ Ya dejaste una reseña para este producto", "error")
        return redirect(url_for("shop.product_detail", slug=slug))

    # Obtener datos del formulario
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()

    # Validar calificación
    if not rating or rating < 1 or rating > 5:
        flash("❌ La calificación debe estar entre 1 y 5 estrellas", "error")
        return redirect(url_for("shop.product_detail", slug=slug))

    # Crear reseña
    review = Review(
        user_id=current_user.id,
        product_id=product.id,
        rating=rating,
        comment=comment if comment else None,
        approved=False  # ✅ Requiere aprobación del admin
    )
    db.session.add(review)
    db.session.commit()

    flash(f"📝 ¡Gracias por tu reseña! Será publicada después de ser revisada.", "success")
    return redirect(url_for("shop.product_detail", slug=slug))


@shop_bp.route("/reseñas/<int:review_id>/eliminar", methods=["POST"])
@login_required
def delete_review(review_id):
    """Elimina una reseña (solo el dueño o admin)."""
    review = Review.query.get_or_404(review_id)

    # Validar permisos
    if review.user_id != current_user.id and not current_user.is_admin:
        flash("❌ No tienes permiso para eliminar esta reseña", "error")
        return redirect(url_for("shop.product_detail", slug=review.product.slug))

    product_slug = review.product.slug
    db.session.delete(review)
    db.session.commit()

    flash("✅ Reseña eliminada", "success")
    return redirect(url_for("shop.product_detail", slug=product_slug))