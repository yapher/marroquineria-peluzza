"""
Servicio de emails.
- Método PRINCIPAL: Gmail vía SMTP (Flask-Mail, TLS puerto 587) — GRATIS
- Respaldo automático: Resend (solo si configurás RESEND_API_KEY)
- Nunca rompe la app si el email falla
"""
import os
from flask import render_template, current_app


def _send_with_gmail(subject: str, recipients: list[str], html_content: str) -> bool:
    """Envía usando Gmail (Flask-Mail / SMTP TLS). Síncrono para saber si falló."""
    try:
        from flask_mail import Message
        from ..extensions import mail

        msg = Message(subject=subject, recipients=recipients)
        msg.html = html_content
        mail.send(msg)

        print(f"   ✅ [GMAIL] Email enviado a: {recipients}")
        return True
    except Exception as e:
        print(f"   ❌ [GMAIL] Error enviando: {e}")
        current_app.logger.error(f"[GMAIL] Error: {e}")
        return False


def _send_with_resend(subject: str, recipients: list[str], html_content: str) -> bool:
    """Respaldo opcional: Resend API (solo si RESEND_API_KEY está configurada)."""
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return False
        resend.api_key = api_key

        sender = os.getenv("MAIL_DEFAULT_SENDER", "onboarding@resend.dev")
        response = resend.Emails.send({
            "from": sender,
            "to": recipients,
            "subject": subject,
            "html": html_content,
        })
        print(f"   ✅ [RESEND] Email enviado. ID: {response.get('id', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ❌ [RESEND] Error: {e}")
        return False


def send_email(subject: str, recipients: list[str], template: str, **context):
    """Envía un email. Prueba Gmail primero; si falla, usa Resend como respaldo."""
    try:
        print(f"\n📧 Enviando email → {recipients} | Asunto: {subject}")

        # Limpiar destinatarios con formato "Nombre <email>"
        cleaned_recipients = []
        for recipient in recipients:
            if '<' in recipient and '>' in recipient:
                cleaned_recipients.append(recipient.split('<')[1].split('>')[0])
            else:
                cleaned_recipients.append(recipient)

        # Renderizar plantilla HTML
        html_content = render_template(template, **context)

        # 1) GMAIL (método principal)
        if os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD"):
            if _send_with_gmail(subject, cleaned_recipients, html_content):
                return True

        # 2) RESEND (respaldo automático si Gmail falló)
        if os.getenv("RESEND_API_KEY"):
            print("   ⚠️ Gmail falló, intentando con Resend...")
            if _send_with_resend(subject, cleaned_recipients, html_content):
                return True

        print("   ⚠️ No se pudo enviar el email (ningún método disponible)")
        return False

    except Exception as e:
        print(f"\n❌ ERROR preparando email: {e}")
        current_app.logger.error(f"❌ Error preparando email: {e}")
        return False


# ============================================
# Funciones específicas (wrappers)
# ============================================
def send_order_confirmation(order):
    """Email de confirmación de pedido."""
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
    """Email cuando cambia el estado del pedido."""
    return send_email(
        subject=f"Actualización de tu pedido #{order.id} - {order.status_display}",
        recipients=[order.customer_email],
        template="emails/order_status_update.html",
        order=order,
        old_status=old_status,
        new_status=new_status,
    )


def send_contact_email(name: str, email: str, subject: str, message: str):
    """Envía el formulario de contacto al admin."""
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
    """Notifica que la reseña fue aprobada."""
    return send_email(
        subject=f"⭐ Tu reseña fue publicada - {review.product.name}",
        recipients=[review.user.email],
        template="emails/review_approved.html",
        review=review,
    )