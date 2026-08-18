# app/blueprints/checkout/routes.py
"""
Rutas del flujo de compra.
Cada ruta delega la lógica de negocio a los servicios
y solo maneja la capa HTTP (request/response).

⚠️ Todas las rutas del carrito y checkout requieren login.
"""
from flask import render_template, request, flash, redirect, url_for, session, current_app, abort
from flask_login import current_user, login_required

from . import checkout_bp
from ...services.cart_service import Cart
from ...services.checkout_service import validate_cart_stock, create_order, cleanup_failed_order
from ...services.discount_calculator import calculate_all_discounts, validate_coupon
from ...services.mercadopago_service import create_preference, verify_payment
from ...services.order_service import confirm_order_payment
from ...services.email_service import send_admin_new_order_notification
from ...models import Product, Order
from ...forms.checkout_forms import CheckoutForm
from ...extensions import db, csrf
from ...config.constants import OrderStatus


# ============================================
# CARRITO (requiere login)
# ============================================
@checkout_bp.route("/carrito")
@login_required
def view_cart():
    cart = Cart()
    return render_template("checkout/cart.html", cart=cart)


@csrf.exempt
@checkout_bp.route("/agregar/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    
    quantity = request.form.get("quantity", 1, type=int)

    cart = Cart()
    cart.add(product_id, quantity)

    if request.headers.get('HX-Request'):
        return render_template("partials/cart_count.html", count=cart.total_items)

    flash(f"✅ {product.name} agregado al carrito.", "success")
    return redirect(url_for("checkout.view_cart"))


@csrf.exempt
@checkout_bp.route("/carrito/update", methods=["POST"])
@login_required
def update_cart():
    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity", type=int)

    cart = Cart()
    cart.update(product_id, quantity)

    return render_template("partials/cart_body.html", cart=Cart())


@csrf.exempt
@checkout_bp.route("/carrito/remove/<int:product_id>", methods=["POST"])
@login_required
def remove_from_cart(product_id):
    cart = Cart()
    cart.remove(product_id)

    if request.headers.get('HX-Request'):
        return render_template("partials/cart_body.html", cart=Cart())

    flash("Producto eliminado del carrito.", "info")
    return redirect(url_for("checkout.view_cart"))


# ============================================
# CHECKOUT (requiere login)
# ============================================
@checkout_bp.route("/checkout")
@login_required
def checkout_page():
    cart = Cart()

    if cart.total_items == 0:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for("checkout.view_cart"))

    form = CheckoutForm()
    if current_user.is_authenticated:
        form.email.data = current_user.email
        form.name.data = current_user.full_name

    coupon_code = session.get("coupon_code")
    user = current_user if current_user.is_authenticated else None
    discounts = calculate_all_discounts(cart.total_price, coupon_code, user)

    return render_template(
        "checkout/checkout.html",
        cart=cart,
        form=form,
        coupon_code=coupon_code,
        coupon_discount=discounts["coupon_discount"],
        level_discount=discounts["level_discount"],
        shipping_cost=discounts["shipping_cost"],
    )


# ============================================
# CUPONES (requiere login)
# ============================================
@checkout_bp.route("/aplicar-cupon", methods=["POST"])
@login_required
def apply_coupon():
    code = request.form.get("code", "").strip().upper()
    cart = Cart()

    valid, message = validate_coupon(code, cart.total_price)
    if not valid:
        flash(message, "error")
        return redirect(url_for("checkout.checkout_page"))

    session["coupon_code"] = code
    flash(f"✅ Cupón '{code}' aplicado exitosamente", "success")
    return redirect(url_for("checkout.checkout_page"))


@checkout_bp.route("/quitar-cupon")
@login_required
def remove_coupon():
    session.pop("coupon_code", None)
    flash("Cupón removido", "info")
    return redirect(url_for("checkout.checkout_page"))


# ============================================
# PROCESAR PEDIDO → MERCADO PAGO (requiere login)
# ============================================
@checkout_bp.route("/checkout/procesar", methods=["POST"])
@login_required
def process_checkout():
    """Crea la orden y redirige al Checkout Pro de Mercado Pago."""
    cart = Cart()

    if cart.total_items == 0:
        flash("Tu carrito está vacío", "error")
        return redirect(url_for("checkout.view_cart"))

    form = CheckoutForm()
    if not form.validate_on_submit():
        flash("Por favor completa todos los campos requeridos", "error")
        return redirect(url_for("checkout.checkout_page"))

    # 1. Validar stock
    valid, product_name = validate_cart_stock(cart)
    if not valid:
        flash(f"❌ Stock insuficiente de '{product_name}'.", "error")
        return redirect(url_for("checkout.view_cart"))

    # 2. Crear orden (delegado al servicio)
    user = current_user if current_user.is_authenticated else None
    order = create_order(
        cart=cart,
        form_data=form.data,
        user=user,
        coupon_code=session.get("coupon_code"),
    )

    # 3. Notificar al admin (best effort)
    try:
        send_admin_new_order_notification(order)
    except Exception as e:
        current_app.logger.error(f"❌ Error enviando email al admin: {e}")

    # 4. Crear preferencia de pago en Mercado Pago
    preference = create_preference(order)
    if not preference:
        cleanup_failed_order(order)
        flash("❌ Hubo un error al conectar con Mercado Pago. Intentá de nuevo.", "error")
        return redirect(url_for("checkout.checkout_page"))

    session["pending_order_id"] = order.id

    # El carrito NO se limpia acá: se limpia recién cuando se confirma el pago
    return redirect(preference["init_point"])


# ============================================
# RETORNO DESDE MERCADO PAGO (sin login_required, MP redirige acá)
# ============================================
@checkout_bp.route("/pago/retorno/<int:order_id>")
def payment_return(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    
    payment_id = request.args.get("payment_id") or request.args.get("collection_id")
    # ... (resto del código igual)
    if not payment_id:
        return redirect(url_for("checkout.payment_failure", order_id=order.id))

    payment = verify_payment(payment_id)

    if payment and payment.get("status") == "approved":
        _confirm_order_payment(order, payment)
        return redirect(url_for("checkout.payment_success", order_id=order.id))

    if payment and payment.get("status") in ("pending", "in_process", "authorized"):
        return redirect(url_for("checkout.payment_pending", order_id=order.id))

    return redirect(url_for("checkout.payment_failure", order_id=order.id))


def _confirm_order_payment(order, payment):
    """
    Confirma el pago delegando al servicio centralizado (order_service),
    y si fue el servicio quien efectivamente confirmó el pago ahora,
    limpia el carrito y las cookies de sesión del comprador.
    """
    was_confirmed = confirm_order_payment(order, payment)
    if not was_confirmed:
        return

    # Limpiar del carrito SOLO los productos comprados
    cart = Cart()
    for item in order.items:
        cart.remove(item.product_id)

    session.pop("pending_order_id", None)
    session.pop("coupon_code", None)


# ============================================
# WEBHOOK DE MERCADO PAGO (server-to-server)
# ============================================
@csrf.exempt
@checkout_bp.route("/webhook/mercadopago", methods=["POST"])
def mercadopago_webhook():
    """
    Recibe notificaciones de Mercado Pago cuando cambia el estado de un pago.
    Siempre responde 200 rápido, incluso ante datos inválidos.
    """
    payment_id = None

    payload = request.get_json(silent=True) or {}
    if payload.get("type") == "payment":
        payment_id = payload.get("data", {}).get("id")

    if not payment_id and request.args.get("topic") == "payment":
        payment_id = request.args.get("id")

    if not payment_id:
        payment_id = request.args.get("data.id") or request.args.get("id")

    if not payment_id:
        current_app.logger.info("Webhook MP: notificación ignorada (sin payment_id).")
        return "", 200

    payment = verify_payment(payment_id)
    if not payment:
        current_app.logger.warning(f"Webhook MP: no se pudo verificar el pago {payment_id}")
        return "", 200

    order_id = payment.get("external_reference")
    if not order_id:
        current_app.logger.warning(f"Webhook MP: pago {payment_id} sin external_reference")
        return "", 200

    order = db.session.get(Order, order_id)
    if not order:
        current_app.logger.warning(f"Webhook MP: orden {order_id} no encontrada (pago {payment_id})")
        return "", 200

    if payment.get("status") == "approved":
        confirm_order_payment(order, payment)

    return "", 200


# ============================================
# PÁGINAS DE RESULTADO
# ============================================
@checkout_bp.route("/pago/exitoso/<int:order_id>")
def payment_success(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    
    if current_user.is_authenticated and order.user_id and order.user_id != current_user.id and not current_user.is_admin:
        # ... (resto del código igual)
        flash("No tienes permiso para ver este pedido", "error")
        return redirect(url_for("main.index"))

    return render_template("checkout/payment_success.html", order=order)


@checkout_bp.route("/pago/pendiente/<int:order_id>")
def payment_pending(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    return render_template("checkout/payment_pending.html", order=order)

@checkout_bp.route("/pago/fallido/<int:order_id>")
def payment_failure(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    return render_template("checkout/payment_failure.html", order=order)

@checkout_bp.route("/pago/reintentar/<int:order_id>", methods=["POST"])
@login_required
def retry_payment(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    
    if order.status != OrderStatus.PENDING_PAYMENT:
        flash("Este pedido ya fue procesado", "warning")
        return redirect(url_for("checkout.payment_success", order_id=order.id))

    preference = create_preference(order)
    if not preference:
        flash("❌ Error al conectar con Mercado Pago", "error")
        return redirect(url_for("main.index"))

    return redirect(preference["init_point"])


@checkout_bp.route("/pago/cancelado")
@login_required
def payment_cancel():
    """Cancela el pedido pendiente. El carrito queda intacto."""
    order_id = session.get("pending_order_id")

    if order_id:
        order = db.session.get(Order, order_id)
        if order and order.status == OrderStatus.PENDING_PAYMENT:
            cleanup_failed_order(order)
            session.pop("pending_order_id", None)
            flash("Pedido cancelado. Tu carrito sigue intacto.", "info")

    return redirect(url_for("checkout.view_cart"))