from flask import render_template, request, flash, redirect, url_for, current_app
from . import main_bp
from ...models import Product


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
    """Formulario de contacto funcional."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Validaciones
        if not name or not email or not message:
            flash("Por favor completa todos los campos obligatorios", "error")
            return render_template('main/contact.html',
                                   name=name, email=email, subject=subject, message=message)

        # Validar formato de email
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Por favor ingresa un email válido", "error")
            return render_template('main/contact.html',
                                   name=name, email=email, subject=subject, message=message)

        # Enviar email al admin
        try:
            from ...services.email_service import send_contact_email
            send_contact_email(name, email, subject, message)
            flash("✅ ¡Mensaje enviado! Te responderemos a la brevedad.", "success")
            return redirect(url_for('main.contact'))
        except Exception as e:
            current_app.logger.error(f"Error enviando email de contacto: {e}")
            flash("❌ Hubo un error al enviar el mensaje. Intenta de nuevo.", "error")

    return render_template('main/contact.html')





from flask import Response
from datetime import datetime


@main_bp.route('/sitemap.xml')
def sitemap():
    """Genera sitemap.xml dinámico con todos los productos, categorías y páginas."""
    from ...models import Product, Category
    
    base_url = request.url_root.rstrip('/')
    pages = []
    
    # Páginas estáticas
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/tienda', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/nosotros', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/envios', 'priority': '0.4', 'changefreq': 'monthly'},
        {'url': '/contacto', 'priority': '0.5', 'changefreq': 'monthly'},
    ]
    for page in static_pages:
        pages.append({
            'loc': f"{base_url}{page['url']}",
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': page['changefreq'],
            'priority': page['priority'],
        })
    
    # Categorías activas
    for cat in Category.query.filter_by(active=True).all():
        pages.append({
            'loc': f"{base_url}/tienda?categoria={cat.slug}",
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.7',
        })
    
    # ✅ CORREGIDO: Usamos created_at en lugar de updated_at
    for product in Product.query.filter_by(active=True).all():
        lastmod = product.created_at.strftime('%Y-%m-%d') if product.created_at else datetime.utcnow().strftime('%Y-%m-%d')
        pages.append({
            'loc': f"{base_url}/tienda/producto/{product.slug}",
            'lastmod': lastmod,
            'changefreq': 'weekly',
            'priority': '0.8',
        })
    
    # Construir XML
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{page["loc"]}</loc>')
        xml.append(f'    <lastmod>{page["lastmod"]}</lastmod>')
        xml.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{page["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    
    return Response('\n'.join(xml), mimetype='application/xml')


@main_bp.route('/robots.txt')
def robots():
    """Indica a los buscadores dónde está el sitemap."""
    sitemap_url = url_for('main.sitemap', _external=True)
    content = f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /auth
Disallow: /cuenta
Disallow: /checkout

Sitemap: {sitemap_url}
"""
    return Response(content, mimetype='text/plain')



