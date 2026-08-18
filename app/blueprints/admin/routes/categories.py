"""Rutas para gestión de categorías."""
from flask import render_template, flash, redirect, url_for, abort
from .. import admin_bp
from ....models import Category
from ....forms.admin_forms import CategoryForm
from ....extensions import db
from . import admin_required, _get_bool
from slugify import slugify


@admin_bp.route("/categorias")
@admin_required
def categories():
    """Lista todas las categorías."""
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=categories)


@admin_bp.route("/categorias/nueva", methods=["GET", "POST"])
@admin_required
def category_new():
    """Crea una nueva categoría."""
    form = CategoryForm()
    if form.validate_on_submit():
        slug = form.slug.data or slugify(form.name.data)
        category = Category(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            active=_get_bool('active')
        )
        db.session.add(category)
        db.session.commit()
        flash(f"✅ Categoría '{category.name}' creada (activa: {category.active})", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, title="Nueva Categoría")


@admin_bp.route("/categorias/<int:category_id>/editar", methods=["GET", "POST"])
@admin_required
def category_edit(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        abort(404)
    
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data or slugify(form.name.data)
        category.description = form.description.data
        category.active = _get_bool('active')
        db.session.commit()
        flash(f"✅ Categoría '{category.name}' actualizada (activa: {category.active})", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, category=category, title="Editar Categoría")