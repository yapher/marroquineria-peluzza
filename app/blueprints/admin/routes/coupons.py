"""Rutas para gestión de cupones de descuento."""
from flask import render_template, request, flash, redirect, url_for, abort
from .. import admin_bp
from ....models import Coupon
from ....forms.coupon_forms import CouponForm
from ....extensions import db
from . import admin_required, _get_bool

@admin_bp.route("/cupones")
@admin_required
def coupons():
    """Lista todos los cupones."""
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template("admin/coupons.html", coupons=coupons)

@admin_bp.route("/cupones/nuevo", methods=["GET", "POST"])
@admin_required
def coupon_new():
    """Crea un nuevo cupón."""
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
            active=_get_bool('active')
        )
        db.session.add(coupon)
        db.session.commit()
        flash(f"✅ Cupón '{coupon.code}' creado (activo: {coupon.active})", "success")
        return redirect(url_for("admin.coupons"))
    
    return render_template("admin/coupon_form.html", form=form, title="Nuevo Cupón")

@admin_bp.route("/cupones/<int:coupon_id>/editar", methods=["GET", "POST"])
@admin_required
def coupon_edit(coupon_id):
    coupon = db.session.get(Coupon, coupon_id)
    if coupon is None:
        abort(404)
    
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
        coupon.active = _get_bool('active')
        
        db.session.commit()
        flash(f"✅ Cupón '{coupon.code}' actualizado (activo: {coupon.active})", "success")
        return redirect(url_for("admin.coupons"))
    
    return render_template("admin/coupon_form.html", form=form, coupon=coupon, title="Editar Cupón")

@admin_bp.route("/cupones/<int:coupon_id>/eliminar", methods=["POST"])
@admin_required
def coupon_delete(coupon_id):
    """Elimina un cupón."""
    # ✅ CORREGIDO: Reemplazado Coupon.query.get_or_404 por db.session.get
    coupon = db.session.get(Coupon, coupon_id)
    if coupon is None:
        abort(404)
        
    db.session.delete(coupon)
    db.session.commit()
    flash(f"✅ Cupón '{coupon.code}' eliminado", "success")
    return redirect(url_for("admin.coupons"))