# app/blueprints/account/routes.py
"""Rutas de la cuenta de usuario: perfil, pedidos, favoritos, fidelización y contraseña."""
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from . import account_bp
from ...models import Order, Product, Wishlist
from ...forms.account_forms import ChangePasswordForm
from ...extensions import db

# ============================================
# PERFIL Y PEDIDOS
# ============================================

@account_bp.route("/")
@login_required
def profile():
    return render_template("account/profile.html")

@account_bp.route("/pedidos")
@login_required
def orders():
    user_orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("account/orders.html", orders=user_orders)

@account_bp.route("/pedidos/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order and current_user.is_admin:
        # ✅ CORREGIDO: Reemplazado Order.query.get_or_404 por db.session.get
        order = db.session.get(Order, order_id)
        if order is None:
            abort(404)
            
    if not order:
        flash("No tienes permiso para ver este pedido o no existe.", "error")
        return redirect(url_for("account.orders"))
        
    return render_template("account/order_detail.html", order=order)

# ============================================
# FAVORITOS (WISHLIST)
# ============================================

@account_bp.route("/favoritos")
@login_required
def wishlist():
    wishlist_items = (
        Wishlist.query
        .filter_by(user_id=current_user.id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )
    return render_template("account/wishlist.html", wishlist_items=wishlist_items)

def _wishlist_response(product: Product, message: str, category: str):
    """Respuesta HTMX (botón) o normal (flash + redirect) para favoritos."""
    if request.headers.get('HX-Request'):
        return render_template("partials/wishlist_button.html", product=product, message=message)
    flash(message, category)
    return redirect(request.referrer or url_for("account.wishlist"))

@account_bp.route("/favoritos/agregar/<int:product_id>", methods=["POST"])
@login_required
def add_to_wishlist(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
        
    existing = Wishlist.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    
    if existing:
        message = f"'{product.name}' ya está en tus favoritos"
    else:
        db.session.add(Wishlist(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        message = f"✅ '{product.name}' agregado a favoritos"
        
    return _wishlist_response(product, message, "success")

@account_bp.route("/favoritos/quitar/<int:product_id>", methods=["POST"])
@login_required
def remove_from_wishlist(product_id):
    wishlist_item = Wishlist.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first_or_404()
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    product = db.session.get(Product, product_id)
    message = f"'{product.name}' quitado de favoritos"
    return _wishlist_response(product, message, "info")

@account_bp.route("/favoritos/count")
@login_required
def wishlist_count():
    return render_template("partials/wishlist_count.html", count=current_user.wishlist_count)

# ============================================
# FIDELIZACIÓN
# ============================================

@account_bp.route("/fidelizacion")
@login_required
def loyalty():
    return render_template("account/loyalty.html")

# ============================================
# CAMBIO DE CONTRASEÑA
# ============================================

@account_bp.route("/cambiar-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("✅ Contraseña actualizada exitosamente", "success")
        return redirect(url_for("account.profile"))
        
    # Mostrar errores de validación como flash en POST fallido
    if request.method == "POST" and form.errors:
        for errors in form.errors.values():
            for error in errors:
                flash(f"❌ {error}", "error")
                
    return render_template("account/change_password.html", form=form)