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


# ============================================
# RUTA TEMPORAL PARA CREAR ADMIN
# ⚠️ ELIMINAR DESPUÉS DE USAR
# ============================================
@main_bp.route("/force-create-admin")
def force_create_admin():
    """Crea el admin automáticamente al visitar esta URL."""
    from ...extensions import db
    from ...models import User, Product, Category
    from werkzeug.security import generate_password_hash

    resultados = []

    try:
        # ========== CREAR ADMIN ==========
        admin_email = "admin@peluzza.com"
        admin_password = "Admin123!"

        admin_existente = User.query.filter_by(is_admin=True).first()

        if admin_existente:
            admin_existente.password_hash = generate_password_hash(admin_password)
            db.session.commit()
            resultados.append(f"✅ Admin actualizado: {admin_existente.email}")
            resultados.append(f"🔑 Nueva contraseña: Admin123!")
        else:
            nuevo_admin = User(
                email=admin_email,
                first_name="Admin",
                last_name="Peluzza",
                is_admin=True
            )
            nuevo_admin.password_hash = generate_password_hash(admin_password)
            db.session.add(nuevo_admin)
            db.session.commit()
            resultados.append(f"✅✅✅ ADMIN CREADO ✅✅✅")
            resultados.append(f"📧 Email: {admin_email}")
            resultados.append(f"🔑 Password: {admin_password}")

        # ========== CREAR PRODUCTOS SI NO HAY ==========
        if Product.query.count() == 0:
            categorias_data = [
                {"name": "Billeteras", "slug": "billeteras", "description": "Billeteras de cuero", "active": True},
                {"name": "Bolsos", "slug": "bolsos", "description": "Bolsos artesanales", "active": True},
                {"name": "Cinturones", "slug": "cinturones", "description": "Cinturones de cuero", "active": True},
            ]
            categorias = {}
            for c in categorias_data:
                cat = Category.query.filter_by(slug=c["slug"]).first()
                if not cat:
                    cat = Category(**c)
                    db.session.add(cat)
                    db.session.commit()
                categorias[c["slug"]] = cat

            productos_data = [
                {"name": "Billetera Clásica", "slug": "billetera-clasica", "description": "Cuero genuino", "price": 45.00, "stock": 15, "sku": "BIL-001", "featured": True, "active": True, "category": categorias["billeteras"]},
                {"name": "Bolso Tote", "slug": "bolso-tote", "description": "Bolso espacioso", "price": 120.00, "stock": 8, "sku": "BOL-001", "featured": True, "active": True, "category": categorias["bolsos"]},
                {"name": "Cinturón Rústico", "slug": "cinturon-rustico", "description": "Cuero grueso", "price": 35.00, "stock": 20, "sku": "CIN-001", "featured": True, "active": True, "category": categorias["cinturones"]},
            ]
            for p in productos_data:
                db.session.add(Product(**p))
            db.session.commit()
            resultados.append("✅ 3 PRODUCTOS CREADOS")
        else:
            resultados.append(f"ℹ️ Ya hay {Product.query.count()} productos")

    except Exception as e:
        resultados.append(f"❌ ERROR: {str(e)}")
        db.session.rollback()

    html = f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 30px; background: #f0fdf4; border: 3px solid #16a34a; border-radius: 12px;">
        <h1>🚀 Setup Completado</h1>
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
            {'<br>'.join(resultados)}
        </div>
        <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🔐 Credenciales:</h3>
            <p><strong>Email:</strong> admin@peluzza.com</p>
            <p><strong>Password:</strong> Admin123!</p>
        </div>
        <a href="/auth/login" style="display: inline-block; background: #9a5f28; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
            Ir a Iniciar Sesión →
        </a>
    </body>
    </html>
    """
    return html

from flask import Response

@main_bp.route("/sitemap.xml")
def sitemap():
    """Sitemap dinámico para Google."""
    from datetime import datetime
    from ...models import Product, Category
    
    base_url = request.host_url.rstrip('/')
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Páginas estáticas
    static_pages = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/tienda', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/nosotros', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/envios', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/contacto', 'priority': '0.7', 'changefreq': 'monthly'},
    ]
    
    for page in static_pages:
        xml += '  <url>\n'
        xml += f'    <loc>{base_url}{page["url"]}</loc>\n'
        xml += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
        xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml += f'    <priority>{page["priority"]}</priority>\n'
        xml += '  </url>\n'
    
    # Categorías
    categories = Category.query.filter_by(active=True).all()
    for cat in categories:
        xml += '  <url>\n'
        xml += f'    <loc>{base_url}/tienda?categoria={cat.slug}</loc>\n'
        xml += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
        xml += '    <changefreq>weekly</changefreq>\n'
        xml += '    <priority>0.8</priority>\n'
        xml += '  </url>\n'
    
    # Productos (los más importantes para SEO)
    products = Product.query.filter_by(active=True).all()
    for product in products:
        last_mod = product.updated_at.strftime("%Y-%m-%d") if product.updated_at else datetime.utcnow().strftime("%Y-%m-%d")
        xml += '  <url>\n'
        xml += f'    <loc>{base_url}/tienda/producto/{product.slug}</loc>\n'
        xml += f'    <lastmod>{last_mod}</lastmod>\n'
        xml += '    <changefreq>weekly</changefreq>\n'
        xml += '    <priority>0.9</priority>\n'
        xml += '  </url>\n'
    
    xml += '</urlset>'
    
    return Response(xml, mimetype='application/xml')


@main_bp.route("/robots.txt")
def robots():
    """Archivo robots.txt para buscadores."""
    base_url = request.host_url.rstrip('/')
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /checkout/
Disallow: /cuenta/
Disallow: /api/

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content, mimetype='text/plain')