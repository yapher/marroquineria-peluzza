"""
Servicio de emails.
- En producción (Render): usa Resend (API HTTP). Mientras el dominio no esté
  verificado en Resend, SOLO se puede enviar al email de la cuenta de Resend
  (RESEND_ACCOUNT_EMAIL). A cualquier otro destinatario se omite el envío
  sin romper el flujo de la app.
- En desarrollo local: usa Gmail SMTP.
- Nunca lanza excepciones: siempre devuelve True/False.
"""
import os
from flask import render_template, current_app

# Mientras no tengas dominio verificado en Resend, esta es la única
# dirección a la que Resend te deja mandar. Cambiala si usás otra cuenta.
RESEND_SANDBOX_EMAIL = os.getenv("MAIL_USERNAME", "marroquineriapeluzza@gmail.com").lower()


def _send_with_gmail(subject: str, recipients: list[str], html_content: str) -> bool:
    """Envía usando Gmail (Flask-Mail / SMTP TLS). Solo tiene sentido en local."""
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
    """
    Envía vía Resend. Filtra automáticamente los destinatarios que Resend
    rechazaría por estar en modo sandbox (dominio no verificado), en vez
    de fallar con un error de la API.
    """
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return False
        resend.api_key = api_key

        # ⚠️ Sin dominio verificado, Resend rechaza cualquier "from" que
        # no sea @resend.dev, y solo entrega a RESEND_SANDBOX_EMAIL.
        sender = "Marroquinería Artesanal <onboarding@resend.dev>"

        allowed = [r for r in recipients if r.strip().lower() == RESEND_SANDBOX_EMAIL]
        blocked = [r for r in recipients if r.strip().lower() != RESEND_SANDBOX_EMAIL]

        if blocked:
            print(f"   ⚠️  [RESEND] Modo sandbox: se omite el envío a {blocked} "
                  f"(solo se puede mandar a {RESEND_SANDBOX_EMAIL} hasta verificar un dominio)")

        if not allowed:
            # No hay a quién mandarle en modo sandbox: no es un error real,
            # simplemente no se puede enviar todavía.
            return False

        response = resend.Emails.send({
            "from": sender,
            "to": allowed,
            "subject": subject,
            "html": html_content,
        })
        print(f"   ✅ [RESEND] Email enviado a {allowed}. ID: {response.get('id', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ❌ [RESEND] Error: {e}")
        return False


def send_email(subject: str, recipients: list[str], template: str, **context):
    """
    Envía un email probando el método adecuado según el entorno.
    Nunca lanza excepciones: si no se pudo enviar, devuelve False y sigue
    la ejecución normal de la app (el pedido, registro, etc. no se ven afectados).
    """
    try:
        print(f"\n📧 Enviando email → {recipients} | Asunto: {subject}")

        cleaned_recipients = []
        for recipient in recipients:
            if '<' in recipient and '>' in recipient:
                cleaned_recipients.append(recipient.split('<')[1].split('>')[0])
            else:
                cleaned_recipients.append(recipient)

        html_content = render_template(template, **context)

        is_production = current_app.config.get("DEBUG") is False
        has_resend = bool(os.getenv("RESEND_API_KEY"))
        has_gmail = bool(os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD"))

        if is_production:
            # En producción NO se intenta Gmail: Render suele bloquear SMTP
            # saliente, y solo demoraría la respuesta hasta el timeout.
            if has_resend:
                return _send_with_resend(subject, cleaned_recipients, html_content)
            print("   ⚠️  No hay RESEND_API_KEY configurada, no se puede enviar el email")
            return False
        else:
            if has_gmail and _send_with_gmail(subject, cleaned_recipients, html_content):
                return True
            if has_resend:
                return _send_with_resend(subject, cleaned_recipients, html_content)
            return False

    except Exception as e:
        print(f"\n❌ ERROR preparando email: {e}")
        current_app.logger.error(f"❌ Error preparando email: {e}")
        return False


# ============================================
# Funciones específicas (wrappers) — sin cambios
# ============================================
def send_order_confirmation(order):
    return send_email(
        subject=f"Confirmación de pedido #{order.id} - Marroquinería Artesanal",
        recipients=[order.customer_email],
        template="emails/order_confirmation.html",
        order=order,
    )


def send_welcome_email(user):
    return send_email(
        subject="¡Bienvenido/a a Marroquinería Artesanal!",
        recipients=[user.email],
        template="emails/welcome.html",
        user=user,
    )


def send_order_status_update(order, old_status: str, new_status: str):
    return send_email(
        subject=f"Actualización de tu pedido #{order.id} - {order.status_display}",
        recipients=[order.customer_email],
        template="emails/order_status_update.html",
        order=order,
        old_status=old_status,
        new_status=new_status,
    )


def send_contact_email(name: str, email: str, subject: str, message: str):
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
    return send_email(
        subject=f"⭐ Tu reseña fue publicada - {review.product.name}",
        recipients=[review.user.email],
        template="emails/review_approved.html",
        review=review,
    )