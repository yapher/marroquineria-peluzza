# app/services/email_service.py
"""
Servicio de emails (orquestador).

Delega el envío real a los providers (Gmail, Resend).
- En producción (Render): usa Resend (API HTTP).
- En desarrollo local: usa Gmail SMTP.
- Nunca lanza excepciones: siempre devuelve True/False.

Los wrappers (send_order_confirmation, send_welcome_email, etc.)
se mantienen acá para no romper los imports existentes.
"""
import os
from flask import render_template, current_app
from .email_providers import gmail_provider, resend_provider


def send_email(subject: str, recipients: list[str], template: str, **context) -> bool:
    """
    Envía un email probando el método adecuado según el entorno.
    Nunca lanza excepciones: si no se pudo enviar, devuelve False y sigue
    la ejecución normal de la app.
    """
    try:
        print(f"\n📧 Enviando email → {recipients} | Asunto: {subject}")

        # Limpiar destinatarios (por si vienen en formato "Nombre <email>")
        cleaned_recipients = []
        for recipient in recipients:
            if '<' in recipient and '>' in recipient:
                cleaned_recipients.append(recipient.split('<')[1].split('>')[0])
            else:
                cleaned_recipients.append(recipient)

        # Renderizar el template HTML
        html_content = render_template(template, **context)

        # Determinar qué provider usar según el entorno
        is_production = current_app.config.get("DEBUG") is False
        has_resend = bool(os.getenv("RESEND_API_KEY"))
        has_gmail = bool(os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD"))

        if is_production:
            if has_resend:
                return resend_provider.send(subject, cleaned_recipients, html_content)
            print("   ⚠️  No hay RESEND_API_KEY configurada, no se puede enviar el email")
            return False
        else:
            # En desarrollo: intentar Gmail primero, luego Resend como fallback
            if has_gmail and gmail_provider.send(subject, cleaned_recipients, html_content):
                return True
            if has_resend:
                return resend_provider.send(subject, cleaned_recipients, html_content)
            return False

    except Exception as e:
        print(f"\n❌ ERROR preparando email: {e}")
        current_app.logger.error(f"❌ Error preparando email: {e}")
        return False


# ============================================
# Funciones específicas (wrappers)
# ============================================

def send_order_confirmation(order):
    """Email de confirmación de pedido al cliente."""
    return send_email(
        subject=f"Confirmación de pedido #{order.id} - Marroquinería Artesanal",
        recipients=[order.customer_email],
        template="emails/order_confirmation.html",
        order=order,
    )


def send_welcome_email(user):
    """Email de bienvenida al registrarse."""
    return send_email(
        subject="¡Bienvenido/a a Marroquinería Artesanal!",
        recipients=[user.email],
        template="emails/welcome.html",
        user=user,
    )


def send_order_status_update(order, old_status: str, new_status: str):
    """Email de actualización de estado del pedido."""
    return send_email(
        subject=f"Actualización de tu pedido #{order.id} - {order.status_display}",
        recipients=[order.customer_email],
        template="emails/order_status_update.html",
        order=order,
        old_status=old_status,
        new_status=new_status,
    )


def send_contact_email(name: str, email: str, subject: str, message: str):
    """Email de contacto al administrador."""
    admin_email = current_app.config.get('MAIL_USERNAME', 'marroquineriapeluzza@gmail.com')
    return send_email(
        subject=f"📬 Nuevo mensaje de contacto: {subject or 'Sin asunto'}",
        recipients=[admin_email],
        template="emails/contact_notification.html",
        name=name,
        email=email,
        contact_subject=subject,
        message=message,
    )


def send_review_approved(review):
    """Email al usuario cuando su reseña es aprobada."""
    return send_email(
        subject=f"⭐ Tu reseña fue publicada - {review.product.name}",
        recipients=[review.user.email],
        template="emails/review_approved.html",
        review=review,
    )


def send_admin_new_order_notification(order):
    """Email al administrador cuando se crea un nuevo pedido."""
    admin_email = current_app.config.get('ADMIN_EMAIL') or current_app.config.get('MAIL_USERNAME')
    if not admin_email:
        current_app.logger.warning("⚠️ ADMIN_EMAIL no está configurado. No se envió la notificación.")
        return False

    return send_email(
        subject=f"📦 ¡Nuevo pedido recibido! #{order.id} - {order.customer_name}",
        recipients=[admin_email],
        template="emails/new_order_admin.html",
        order=order,
    )