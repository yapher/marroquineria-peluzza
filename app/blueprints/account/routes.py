# app/blueprints/account/routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from . import account_bp
from ...models import Order, Product, Wishlist
from ...extensions import db, csrf

@account_bp.route("/")
@login_required
def profile():
    return render_template("account/profile.html")

@account_bp.route("/pedidos")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("account/orders.html", orders=user_orders)

@account_bp.route("/pedidos/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    
    if not order and current_user.is_admin:
        order = Order.query.get_or_404(order_id)
        
    if not order:
        flash("No tienes permiso para ver este pedido o no existe.", "error")
        return redirect(url_for("account.orders"))
        
    return render_template("account/order_detail.html", order=order)

from flask import request
from ...models import Product, Wishlist


@account_bp.route("/favoritos")
@login_required
def wishlist():
    """Muestra la lista de deseos del usuario."""
    wishlist_items = (
        Wishlist.query
        .filter_by(user_id=current_user.id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )
    return render_template("account/wishlist.html", wishlist_items=wishlist_items)

@csrf.exempt
@account_bp.route("/favoritos/agregar/<int:product_id>", methods=["POST"])
@login_required
def add_to_wishlist(product_id):
    """Agrega un producto a la wishlist."""
    product = Product.query.get_or_404(product_id)
    
    # Verificar si ya está en la wishlist
    existing = Wishlist.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    
    if existing:
        message = f"'{product.name}' ya está en tus favoritos"
    else:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        message = f"✅ '{product.name}' agregado a favoritos"
    
    # Si es petición HTMX, devolver solo el contador y botón actualizado
    if request.headers.get('HX-Request'):
        return render_template(
            "partials/wishlist_button.html",
            product=product,
            message=message
        )
    
    flash(message, "success")
    return redirect(request.referrer or url_for("account.wishlist"))

@csrf.exempt
@account_bp.route("/favoritos/quitar/<int:product_id>", methods=["POST"])
@login_required
def remove_from_wishlist(product_id):
    """Quita un producto de la wishlist."""
    wishlist_item = Wishlist.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first_or_404()
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    product = Product.query.get(product_id)
    message = f"'{product.name}' quitado de favoritos"
    
    if request.headers.get('HX-Request'):
        return render_template(
            "partials/wishlist_button.html",
            product=product,
            message=message
        )
    
    flash(message, "info")
    return redirect(request.referrer or url_for("account.wishlist"))


@account_bp.route("/favoritos/count")
@login_required
def wishlist_count():
    """Devuelve el contador de favoritos para HTMX."""
    return render_template(
        "partials/wishlist_count.html",
        count=current_user.wishlist_count
    )


@account_bp.route("/fidelizacion")
@login_required
def loyalty():
    """Página del programa de fidelización."""
    return render_template("account/loyalty.html")