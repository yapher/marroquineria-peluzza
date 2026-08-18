# app/blueprints/admin/routes/products.py
"""Rutas para gestión de productos e imágenes."""
from flask import render_template, request, flash, redirect, url_for, current_app, abort
from .. import admin_bp
from ....models import Product, ProductImage
from ....forms.admin_forms import ProductForm
from ....extensions import db
from ....services.storage_service import upload_image, delete_image
from ....services.product_image_service import process_extra_images, set_primary_image
from . import admin_required, _get_bool
from slugify import slugify


# ============================================
# LISTADO Y CREACIÓN
# ============================================

@admin_bp.route("/productos")
@admin_required
def products():
    """Lista todos los productos."""
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=products)


@admin_bp.route("/productos/nuevo", methods=["GET", "POST"])
@admin_required
def product_new():
    """Crea un nuevo producto."""
    form = ProductForm()

    if form.validate_on_submit():
        slug = form.slug.data or slugify(form.name.data)
        image_file = request.files.get('image')
        extra_files = request.files.getlist('extra_images')

        image_url = None
        if image_file and image_file.filename and image_file.filename != '':
            image_url = upload_image(image_file)
            if not image_url:
                flash("⚠️ No se pudo subir la imagen principal.", "warning")

        is_handmade = _get_bool('is_handmade')
        featured = _get_bool('featured')
        active = _get_bool('active')

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
            is_handmade=is_handmade,
            featured=featured,
            active=active,
            image_url=image_url
        )
        db.session.add(product)
        db.session.flush()

        extra_count = process_extra_images(extra_files, product)

        db.session.commit()

        msg = f"✅ Producto '{product.name}' creado"
        if image_url:
            msg += " con imagen principal"
        if extra_count > 0:
            msg += f" (+{extra_count} imagen(es) en galería)"
        flash(msg, "success")

        return redirect(url_for("admin.products"))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"❌ Error en '{field}': {error}", "error")

    return render_template(
        "admin/product_form.html", form=form, title="Nuevo Producto",
        max_extra_images=current_app.config.get("MAX_EXTRA_IMAGES", 8),
        max_image_size_mb=current_app.config.get("MAX_IMAGE_SIZE_MB", 5),
    )


# ============================================
# EDICIÓN Y ELIMINACIÓN
# ============================================

@admin_bp.route("/productos/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    
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
        product.is_handmade = _get_bool('is_handmade')
        product.featured = _get_bool('featured')
        product.active = _get_bool('active')

        # Imagen principal
        file = request.files.get('image')
        if file and file.filename and file.filename != '':
            new_url = upload_image(file)
            if new_url:
                delete_image(product.image_url)
                product.image_url = new_url
            else:
                flash("⚠️ No se pudo subir la nueva imagen", "warning")

        # Imágenes extra (delegado al servicio)
        extra_files = request.files.getlist('extra_images')
        if extra_files:
            max_position = max([img.position for img in product.images], default=-1)
            extra_count = process_extra_images(extra_files, product, start_position=max_position + 1)
        else:
            extra_count = 0

        db.session.commit()

        msg = f"✅ Producto '{product.name}' actualizado (activo: {product.active})"
        if extra_count > 0:
            msg += f" (+{extra_count} imagen(es) nueva(s))"
        flash(msg, "success")

        return redirect(url_for("admin.product_edit", product_id=product.id))

    if request.method == "POST" and form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"❌ Error en '{field}': {error}", "error")

    return render_template(
        "admin/product_form.html", form=form, product=product, title="Editar Producto",
        max_extra_images=current_app.config.get("MAX_EXTRA_IMAGES", 8),
        max_image_size_mb=current_app.config.get("MAX_IMAGE_SIZE_MB", 5),
    )


@admin_bp.route("/productos/<int:product_id>/eliminar", methods=["POST"])
@admin_required
def product_delete(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    
    product.active = False
    product.featured = False
    db.session.commit()
    flash(f"✅ Producto '{product.name}' desactivado", "success")
    return redirect(url_for("admin.products"))


# ============================================
# GESTIÓN DE IMÁGENES
# ============================================

@admin_bp.route("/productos/<int:product_id>/imagenes/<int:image_id>/eliminar", methods=["POST"])
@admin_required
def product_image_delete(product_id, image_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first_or_404()
    # ... (resto del código igual)
    delete_image(image.url)
    db.session.delete(image)
    db.session.commit()

    flash("✅ Imagen eliminada de la galería", "success")
    return redirect(url_for("admin.product_edit", product_id=product.id))


@admin_bp.route("/productos/<int:product_id>/imagenes/<int:image_id>/principal", methods=["POST"])
@admin_required
def product_image_set_primary(product_id, image_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first_or_404()
    # ... (resto del código igual)
    set_primary_image(product, image)

    return redirect(url_for("admin.product_edit", product_id=product.id))