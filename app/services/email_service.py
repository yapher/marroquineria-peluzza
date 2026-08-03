from flask import render_template, current_app
from flask_mail import Message
from ..extensions import mail


def send_email(subject: str, recipients: list[str], template: str, **context):
    """
    Función genérica para enviar emails con plantillas HTML.
    """
    try:
        print(f"\n📧 INTENTANDO ENVIAR EMAIL...")
        print(f"   Para: {recipients}")
        print(f"   Asunto: {subject}")
        
        # Limpiar el email del remitente si tiene formato "Nombre <email>"
        cleaned_recipients = []
        for recipient in recipients:
            if '<' in recipient and '>' in recipient:
                # Extraer solo el email de "Nombre <email>"
                email_only = recipient.split('<')[1].split('>')[0]
                cleaned_recipients.append(email_only)
            else:
                cleaned_recipients.append(recipient)
        
        msg = Message(
            subject=subject,
            recipients=cleaned_recipients,
        )
        
        # Renderizar plantilla HTML
        msg.html = render_template(template, **context)
        
        # Enviar
        mail.send(msg)
        print(f"   ✅ ¡EMAIL ENVIADO CON ÉXITO! a: {cleaned_recipients}\n")
        return True
        
    except Exception as e:
        print(f"\n   ❌ ERROR CRÍTICO AL ENVIAR EMAIL: {e}\n")
        current_app.logger.error(f"❌ Error enviando email: {e}")
        return False


def send_order_confirmation(order):
    """Envía email de confirmación de pedido."""
    subject = f"Confirmación de pedido #{order.id} - Marroquinería Artesanal"
    
    return send_email(
        subject=subject,
        recipients=[order.customer_email],
        template="emails/order_confirmation.html",
        order=order,
    )


def send_welcome_email(user):
    """Envía email de bienvenida al registrarse."""
    subject = "¡Bienvenido/a a Marroquinería Artesanal!"
    
    return send_email(
        subject=subject,
        recipients=[user.email],
        template="emails/welcome.html",
        user=user,
    )


def send_order_status_update(order, old_status: str, new_status: str):
    """Envía email al cliente cuando cambia el estado del pedido."""
    subject = f"Actualización de tu pedido #{order.id} - {order.status_display}"
    
    return send_email(
        subject=subject,
        recipients=[order.customer_email],
        template="emails/order_status_update.html",
        order=order,
        old_status=old_status,
        new_status=new_status,
    )


def send_contact_email(name: str, email: str, subject: str, message: str):
    """Envía el mensaje del formulario de contacto al admin."""
    final_subject = f"📬 Nuevo mensaje de contacto: {subject or 'Sin asunto'}"
    
    # Email del admin (el destinatario)
    admin_email = current_app.config.get('MAIL_USERNAME', 'marroquineriapeluzza@gmail.com')
    
    return send_email(
        subject=final_subject,
        recipients=[admin_email],
        template="emails/contact_notification.html",
        name=name,
        email=email,
        contact_subject=subject,  # ✅ Renombrado de 'subject' a 'contact_subject'
        message=message,
    )

def send_review_approved(review):
    """Notifica al usuario que su reseña fue aprobada."""
    subject = f"⭐ Tu reseña fue publicada - {review.product.name}"
    
    return send_email(
        subject=subject,
        recipients=[review.user.email],
        template="emails/review_approved.html",
        review=review,
    )