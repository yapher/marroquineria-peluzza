from flask import render_template, request, flash, redirect, url_for, session, current_app
from flask_login import current_user
from decimal import Decimal
from datetime import datetime
from . import checkout_bp
from ...services.cart_service import Cart
from ...models import Product, Order, OrderItem, Coupon, User
from ...forms.checkout_forms import CheckoutForm
from ...extensions import db
from ...services.loyalty_service import award_points_for_order

SHIPPING_COST = Decimal("10.00")


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


@checkout_bp.route("/agregar/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get("quantity", 1, type=int) or 1
    cart = Cart()

    if not product.active:
        flash("❌ Este producto no está disponible.", "error")
    elif product.stock <= 0:
        flash(f"❌ '{product.name}' está agotado.", "error")
    elif cart.get_quantity(product_id) >= product.stock:
        flash(f"❌ No hay más stock de '{product.name}' (máximo {product.stock}).", "warning")
    else:
        cart.add(product_id, quantity)
        flash(f"✅ {product.name} agregado al carrito.", "success")

    if request.headers.get('HX-Request'):
        return render_template("partials/cart_count.html", count=cart.total_items)
    return redirect(request.referrer or url_for("checkout.view_cart"))


@checkout_bp.route("/carrito/update", methods=["POST"])
def update_cart():
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)
    cart = Cart()
    if product_id is not None:
        cart.update(product_id, quantity)
    return render_template("partials/cart_body.html", cart=Cart())


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

    # Cupón
    coupon_code = session.get("coupon_code")
    coupon_discount = Decimal("0")
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon and coupon.is_valid:
            coupon_discount = coupon.apply_discount(cart.total_price)
        else:
            session.pop("coupon_code", None)
            coupon_code = None

    # ✅ Descuento por nivel de fidelización (ahora visible en el resumen)
    level_discount = Decimal("0")
    if current_user.is_authenticated and current_user.loyalty_discount > 0:
        base_for_level = cart.total_price - coupon_discount
        level_discount = base_for_level * Decimal(current_user.loyalty_discount) / Decimal("100")

    return render_template("checkout/checkout.html",
                           cart=cart,
                           form=form,
                           coupon_code=coupon_code,
                           coupon_discount=coupon_discount,
                           level_discount=level_discount,
                           shipping_cost=SHIPPING_COST)


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


@checkout_bp.route("/checkout/procesar", methods=["POST"])
def process_checkout():
    """Crea la orden pendiente y redirige a la página de pago simulado."""
    cart = Cart()
    if cart.total_items == 0:
        flash("Tu carrito está vacío", "error")
        return redirect(url_for("checkout.view_cart"))

    form = CheckoutForm()
    if not form.validate_on_submit():
        flash("Por favor completa todos los campos requeridos", "error")
        return redirect(url_for("checkout.checkout_page"))

    # ✅ Validar stock ANTES de crear la orden
    stock_ok, problem_product = cart.validate_stock()
    if not stock_ok:
        nombre = problem_product.name if problem_product else "un producto"
        flash(f"❌ Stock insuficiente para '{nombre}'. Ajusta tu carrito.", "error")
        return redirect(url_for("checkout.view_cart"))

    subtotal = cart.total_price
    shipping_cost = SHIPPING_COST

    coupon_code = None
    coupon_discount = Decimal("0")
    if "coupon_code" in session:
        coupon = Coupon.query.filter_by(code=session["coupon_code"]).first()
        if coupon and coupon.is_valid and subtotal >= coupon.min_purchase:
            coupon_code = coupon.code
            coupon_discount = coupon.apply_discount(subtotal)

    # Descuento por nivel de fidelización
    level_discount = Decimal("0")
    if current_user.is_authenticated and current_user.loyalty_discount > 0:
        base_for_level = subtotal - coupon_discount
        level_discount = base_for_level * Decimal(current_user.loyalty_discount) / Decimal("100")

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

    # ✅ El carrito NO se limpia acá: se limpia recién al confirmar el pago
    session["pending_order_id"] = order.id
    return redirect(url_for("checkout.simulated_payment", order_id=order.id))


@checkout_bp.route("/checkout/pago-simulado/<int:order_id>")
def simulated_payment(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "pending_payment":
        flash("Este pedido ya fue procesado", "warning")
        return redirect(url_for("checkout.payment_success", order_id=order.id))
    return render_template("checkout/simulated_payment.html", order=order)


@checkout_bp.route("/checkout/confirmar-pago/<int:order_id>", methods=["POST"])
def confirm_payment(order_id):
    """Confirma el pago simulado (modo desarrollo)."""
    order = Order.query.get_or_404(order_id)

    if order.status != "pending_payment":
        flash("Este pedido ya fue procesado", "warning")
        return redirect(url_for("checkout.payment_success", order_id=order.id))

    # ✅ Revalidar stock antes de confirmar (evita stock negativo)
    for item in order.items:
        product = Product.query.get(item.product_id)
        if not product or product.stock < item.quantity:
            order.status = "cancelled"
            db.session.commit()
            session.pop("pending_order_id", None)
            flash("❌ Un producto se quedó sin stock. El pedido se canceló; "
                  "tu carrito sigue cargado para que lo ajustes.", "error")
            return redirect(url_for("checkout.view_cart"))

    order.status = "paid"
    order.payment_method = "stripe_test"
    order.payment_status = "succeeded"
    order.payment_id = f"test_{order.id}_{int(datetime.utcnow().timestamp())}"

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

    # ✅ Limpiar del carrito SOLO los productos comprados (recién ahora)
    cart = Cart()
    for item in order.items:
        cart.remove(item.product_id)

    session.pop("pending_order_id", None)
    session.pop("coupon_code", None)

    try:
        from ...services.email_service import send_order_confirmation
        send_order_confirmation(order)
    except Exception as e:
        current_app.logger.error(f"Error enviando email: {e}")

    flash("✅ ¡Pago confirmado exitosamente!", "success")
    return redirect(url_for("checkout.payment_success", order_id=order.id))


@checkout_bp.route("/checkout/cancelar-pago")
def cancel_payment():
    """Cancela el pago simulado. El carrito queda intacto (ahora es verdad)."""
    order_id = session.get("pending_order_id")
    if order_id:
        order = Order.query.get(order_id)
        if order and order.status == "pending_payment":
            db.session.delete(order)
            db.session.commit()
        session.pop("pending_order_id", None)
    flash("Pago cancelado. Tu carrito sigue intacto.", "info")
    return redirect(url_for("checkout.view_cart"))


@checkout_bp.route("/pago/exitoso/<int:order_id>")
def payment_success(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.is_authenticated and order.user_id != current_user.id and not current_user.is_admin:
        flash("No tienes permiso para ver este pedido", "error")
        return redirect(url_for("main.index"))
    session.pop("pending_order_id", None)
    session.pop("coupon_code", None)
    return render_template("checkout/payment_success.html", order=order)


@checkout_bp.route("/pago/cancelado")
def payment_cancel():
    order_id = session.get("pending_order_id")
    if order_id:
        order = Order.query.get(order_id)
        if order and order.status == "pending_payment":
            db.session.delete(order)
            db.session.commit()
        session.pop("pending_order_id", None)
    flash("Pago cancelado. Tu carrito sigue intacto.", "info")
    return redirect(url_for("checkout.view_cart"))