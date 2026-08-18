# app/blueprints/main/routes.py
"""Rutas públicas principales: inicio, páginas informativas, contacto y SEO."""
from flask import render_template, flash, redirect, url_for, current_app

from . import main_bp
from ...forms.contact_forms import ContactForm
from ...models import Product
from ...services.email_service import send_contact_email
from ...utils.seo import sitemap_response, robots_response


@main_bp.route("/")
def index():
    """Página de inicio con productos destacados."""
    featured_products = Product.query.filter_by(featured=True, active=True).limit(4).all()
    return render_template('index.html', featured_products=featured_products)


@main_bp.route("/nosotros")
def about():
    """Página sobre nosotros y nuestros artesanos."""
    return render_template('main/about.html')


@main_bp.route("/envios")
def shipping():
    """Política de envíos y devoluciones."""
    return render_template('main/shipping.html')


@main_bp.route("/contacto", methods=["GET", "POST"])
def contact():
    """Formulario de contacto (validado con WTForms)."""
    form = ContactForm()

    if form.validate_on_submit():
        try:
            send_contact_email(
                name=form.name.data.strip(),
                email=form.email.data.strip(),
                subject=form.subject.data.strip() if form.subject.data else "",
                message=form.message.data.strip(),
            )
            flash("✅ ¡Mensaje enviado! Te responderemos a la brevedad.", "success")
            return redirect(url_for('main.contact'))
        except Exception as e:
            current_app.logger.error(f"Error enviando email de contacto: {e}")
            flash("❌ Hubo un error al enviar el mensaje. Intenta de nuevo.", "error")

    return render_template('main/contact.html', form=form)


@main_bp.route('/sitemap.xml')
def sitemap():
    """Genera sitemap.xml dinámico con productos, categorías y páginas."""
    return sitemap_response()


@main_bp.route('/robots.txt')
def robots():
    """Indica a los buscadores dónde está el sitemap."""
    return robots_response()