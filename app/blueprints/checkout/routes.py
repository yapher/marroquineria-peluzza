from flask import render_template, request, flash, redirect, url_for, session, current_app
from flask_login import current_user
from decimal import Decimal
from . import checkout_bp
from ...services.cart_service import Cart
from ...models import Product, Order, OrderItem, Coupon, User
from ...forms.checkout_forms import CheckoutForm
from ...extensions import db, csrf
from ...services.loyalty_service import award_points_for_order


# ============================================
# CARRITO (sin cambios)
# ============================================
@checkout_bp.route("/test")
def test_route():
    return "✅ ¡El blueprint de checkout está funcionando!"


@checkout_bp.route("/carrito")
def view_cart():
    cart = Cart()
    return render_template("checkout/cart.html", cart=cart)


@checkout_bp.route("/carrito/count")
def cart_count():
    cart = Cart()
    return render_template("partials/cart_count.html", count=cart.total_items)


@csrf.exempt
@checkout_bp.route("/agregar/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get("quantity", 1, type=int)
    cart = Cart()
    cart.add(product_id, quantity)
    if request.headers.get('HX-Request'):
        return render_template("partials/cart_count.html", count=cart.total_items)
    flash(f"✅ {product.name} agregado al carrito.", "success")
    return redirect(url_for("checkout.view_cart"))


@csrf.exempt
@checkout_bp.route("/carrito/update", methods=["POST"])
def update_cart():
    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity", type=int)
    cart = Cart()
    cart.update(product_id, quantity)
    return render_template("partials/cart_body.html", cart=Cart())


@csrf.exempt
@checkout_bp.route("/carrito/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = Cart()
    cart.remove(product_id)
    if request.headers.get('HX-Request'):
        return render_template("partials/cart_body.html", cart=Cart())
    flash("Producto eliminado del carrito.", "info")
    return redirect(url_for("checkout.view_cart"))


# ============================================
# CHECKOUT
# ============================================
@checkout_bp.route("/checkout")
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
    coupon_discount = Decimal("0")
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon and coupon.is_valid:
            coupon_discount = coupon.apply_discount(cart.total_price)

    return render_template("checkout/checkout.html",
                           cart=cart,
                           form=form,
                           coupon_code=coupon_code,
                           coupon_discount=coupon_discount)


@checkout_bp.route("/aplicar-cupon", methods=["POST"])
def apply_coupon():
    code = request.form.get("code", "").strip().upper()
    if not code:
        flash("Ingresa un código de cupón", "error")
        return redirect(url_for("checkout.checkout_page"))

    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        flash("❌ Cupón no encontrado", "error")
        return redirect(url_for("checkout.checkout_page"))

    if not coupon.is_valid:
        flash("❌ Este cupón ya no es válido", "error")
        return redirect(url_for("checkout.checkout_page"))

    cart = Cart()
    if cart.total_price < coupon.min_purchase:
        flash(f"❌ Compra mínima requerida: ${coupon.min_purchase}", "error")
        return redirect(url_for("checkout.checkout_page"))

    session["coupon_code"] = code
    flash(f"✅ Cupón '{code}' aplicado exitosamente", "success")
    return redirect(url_for("checkout.checkout_page"))


@checkout_bp.route("/quitar-cupon")
def remove_coupon():
    session.pop("coupon_code", None)
    flash("Cupón removido", "info")
    return redirect(url_for("checkout.checkout_page"))


# ============================================
# PROCESAR PEDIDO → MERCADO PAGO
# ============================================
@checkout_bp.route("/checkout/procesar", methods=["POST"])
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

    # ✅ Validar stock antes de crear la orden
    for item in cart.items:
        product = item["product"]
        if product.stock < item["quantity"]:
            flash(f"❌ Stock insuficiente de '{product.name}' (quedan {product.stock} unidades).", "error")
            return redirect(url_for("checkout.view_cart"))

    subtotal = cart.total_price
    shipping_cost = Decimal("10.00")

    coupon_code = None
    coupon_discount = Decimal("0")
    if "coupon_code" in session:
        coupon = Coupon.query.filter_by(code=session["coupon_code"]).first()
        if coupon and coupon.is_valid:
            coupon_code = coupon.code
            coupon_discount = coupon.apply_discount(subtotal)

    # Descuento por nivel de fidelización
    level_discount = Decimal("0")
    if current_user.is_authenticated:
        discount_percent = current_user.loyalty_discount
        if discount_percent > 0:
            base_for_level = subtotal - coupon_discount
            level_discount = base_for_level * Decimal(discount_percent) / Decimal("100")

    total = subtotal + shipping_cost - coupon_discount - level_discount

    order = Order(
        user_id=current_user.id if current_user.is_authenticated else None,
        customer_email=form.email.data,
        customer_name=form.name.data,
        customer_phone=form.phone.data,
        shipping_address=form.address.data,
        shipping_city=form.city.data,
        shipping_state=form.state.data,
        shipping_zip=form.zip_code.data,
        shipping_country=form.country.data,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        coupon_code=coupon_code,
        coupon_discount=coupon_discount,
        level_discount=level_discount,
        status="pending_payment",
        notes=form.notes.data
    )
    db.session.add(order)
    db.session.flush()

    for item in cart.items:
        product = item["product"]
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            quantity=item["quantity"],
            price=product.price
        )
        db.session.add(order_item)
    db.session.commit()

    # ✅ Crear preferencia de pago en Mercado Pago
    from ...services.mercadopago_service import create_preference
    preference = create_preference(order)
    if not preference:
        db.session.delete(order)
        db.session.commit()
        flash("❌ Hubo un error al conectar con Mercado Pago. Intentá de nuevo.", "error")
        return redirect(url_for("checkout.checkout_page"))

    session["pending_order_id"] = order.id

    # ✅ El carrito NO se limpia acá: se limpia recién cuando se confirma el pago
    return redirect(preference["init_point"])


# ============================================
# RETORNO DESDE MERCADO PAGO
# ============================================
@checkout_bp.route("/pago/retorno/<int:order_id>")
def payment_return(order_id):
    """Mercado Pago redirige acá después de pagar."""
    order = Order.query.get_or_404(order_id)

    payment_id = request.args.get("payment_id") or request.args.get("collection_id")

    if not payment_id:
        return redirect(url_for("checkout.payment_failure", order_id=order.id))

    # ✅ VALIDAR el pago con la API de MP (nunca confiar solo en la URL)
    from ...services.mercadopago_service import verify_payment
    payment = verify_payment(payment_id)

    if payment and payment.get("status") == "approved":
        if order.status == "pending_payment":
            _confirm_order_payment(order, payment)
        return redirect(url_for("checkout.payment_success", order_id=order.id))

    if payment and payment.get("status") in ("pending", "in_process", "authorized"):
        return redirect(url_for("checkout.payment_pending", order_id=order.id))

    return redirect(url_for("checkout.payment_failure", order_id=order.id))


def _confirm_order_payment(order, payment):
    """Confirma el pago: stock, puntos, cupón, carrito y email."""
    order.status = "paid"
    order.payment_method = "mercadopago"
    order.payment_status = payment.get("status", "succeeded")
    order.payment_id = str(payment.get("id", ""))

    # Puntos de fidelización
    if order.user_id:
        user = User.query.get(order.user_id)
        award_points_for_order(order, user)

    # Reducir stock
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock -= item.quantity

    # Incrementar uso del cupón
    if order.coupon_code:
        coupon = Coupon.query.filter_by(code=order.coupon_code).first()
        if coupon:
            coupon.uses_count += 1

    db.session.commit()

    # ✅ Limpiar del carrito SOLO los productos comprados
    cart = Cart()
    for item in order.items:
        cart.remove(item.product_id)

    session.pop("pending_order_id", None)
    session.pop("coupon_code", None)

    # Email de confirmación
    try:
        from ...services.email_service import send_order_confirmation
        send_order_confirmation(order)
    except Exception as e:
        current_app.logger.error(f"Error enviando email: {e}")


# ============================================
# PÁGINAS DE RESULTADO
# ============================================
@checkout_bp.route("/pago/exitoso/<int:order_id>")
def payment_success(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.is_authenticated and order.user_id and order.user_id != current_user.id and not current_user.is_admin:
        flash("No tienes permiso para ver este pedido", "error")
        return redirect(url_for("main.index"))
    return render_template("checkout/payment_success.html", order=order)


@checkout_bp.route("/pago/pendiente/<int:order_id>")
def payment_pending(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("checkout/payment_pending.html", order=order)


@checkout_bp.route("/pago/fallido/<int:order_id>")
def payment_failure(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("checkout/payment_failure.html", order=order)


@checkout_bp.route("/pago/reintentar/<int:order_id>", methods=["POST"])
def retry_payment(order_id):
    """Reintenta el pago de un pedido pendiente."""
    order = Order.query.get_or_404(order_id)
    if order.status != "pending_payment":
        flash("Este pedido ya fue procesado", "warning")
        return redirect(url_for("checkout.payment_success", order_id=order.id))

    from ...services.mercadopago_service import create_preference
    preference = create_preference(order)
    if not preference:
        flash("❌ Error al conectar con Mercado Pago", "error")
        return redirect(url_for("main.index"))
    return redirect(preference["init_point"])


@checkout_bp.route("/pago/cancelado")
def payment_cancel():
    """Cancela el pedido pendiente. El carrito queda intacto."""
    order_id = session.get("pending_order_id")
    if order_id:
        order = Order.query.get(order_id)
        if order and order.status == "pending_payment":
            db.session.delete(order)
            db.session.commit()
        session.pop("pending_order_id", None)
    flash("Pedido cancelado. Tu carrito sigue intacto.", "info")
    return redirect(url_for("checkout.view_cart"))