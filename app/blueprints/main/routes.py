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