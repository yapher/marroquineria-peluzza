"""
Servicio de emails.
- Prioridad 1: Resend (API HTTP, funciona en Render)
- Prioridad 2: Flask-Mail async (SMTP tradicional)
- Si nada funciona, suprime silenciosamente sin romper la app
"""
import os
import threading
from flask import render_template, current_app


def _send_with_resend(subject: str, recipients: list[str], html_content: str) -> bool:
    """
    Envía email usando Resend API (HTTP). No se bloquea en Render.
    """
    try:
        import resend
        
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return False
        
        resend.api_key = api_key
        
        # Email remitente
        sender_raw = os.getenv("MAIL_DEFAULT_SENDER", "Marroquinería Peluzza <onboarding@resend.dev>")
        
        # Normalizar sender
        if '<' in sender_raw and '>' in sender_raw:
            sender_email = sender_raw.split('<')[1].split('>')[0]
            sender_name = sender_raw.split('<')[0].strip()
            final_sender = f"{sender_name} <{sender_email}>" if sender_name else sender_raw
        else:
            final_sender = f"Marroquinería Peluzza <{sender_raw}>"
        
        response = resend.Emails.send({
            "from": final_sender,
            "to": recipients,
            "subject": subject,
            "html": html_content,
        })
        
        print(f"   ✅ [RESEND] Email enviado con éxito! ID: {response.get('id', 'N/A')}")
        return True
        
    except ImportError:
        print("   ⚠️  Paquete 'resend' no instalado. Intentando Flask-Mail...")
        return False
    except Exception as e:
        print(f"   ⚠️  Error con Resend: {e}. Intentando Flask-Mail...")
        return False


def _send_with_flask_mail(subject: str, recipients: list[str], html_content: str) -> bool:
    """
    Envía email usando Flask-Mail (SMTP tradicional) de forma asíncrona.
    """
    try:
        from flask_mail import Message
        from ..extensions import mail
        
        msg = Message(subject=subject, recipients=recipients)
        msg.html = html_content
        
        app = current_app._get_current_object()
        
        def _send():
            try:
                with app.app_context():
                    mail.send(msg)
                    print(f"   ✅ [SMTP] Email enviado con éxito a: {recipients}")
            except Exception as e:
                print(f"   ⚠️  [SMTP] Error enviando: {e}")
        
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
        return True
        
    except Exception as e:
        print(f"   ❌ No se pudo preparar Flask-Mail: {e}")
        return False


def send_email(subject: str, recipients: list[str], template: str, **context):
    """
    Envía email usando la mejor estrategia disponible.
    Nunca falla ni bloquea la app.
    """
    try:
        print(f"\n📧 INTENTANDO ENVIAR EMAIL...")
        print(f"   Para: {recipients}")
        print(f"   Asunto: {subject}")
        
        # Si no hay servicio configurado, suprimir silenciosamente
        if not os.getenv("RESEND_API_KEY") and not os.getenv("MAIL_SERVER"):
            print(f"   ℹ️  [SUPRIMIDO] No hay servicio de email configurado")
            print(f"   💡 Configura RESEND_API_KEY o MAIL_SERVER para activar emails\n")
            return True
        
        # Limpiar destinatarios
        cleaned_recipients = []
        for recipient in recipients:
            if '<' in recipient and '>' in recipient:
                email_only = recipient.split('<')[1].split('>')[0]
                cleaned_recipients.append(email_only)
            else:
                cleaned_recipients.append(recipient)
        
        # Renderizar plantilla HTML
        html_content = render_template(template, **context)
        
        # Prioridad 1: Resend (API HTTP - funciona en Render)
        if os.getenv("RESEND_API_KEY"):
            if _send_with_resend(subject, cleaned_recipients, html_content):
                return True
        
        # Prioridad 2: Flask-Mail (SMTP - fallback)
        if _send_with_flask_mail(subject, cleaned_recipients, html_content):
            return True
        
        print("   ⚠️  Ningún servicio de email disponible")
        return False
        
    except Exception as e:
        print(f"\n   ❌ ERROR preparando email: {e}\n")
        current_app.logger.error(f"❌ Error preparando email: {e}")
        return False


# ============================================
# Funciones específicas (wrappers)
# ============================================

def send_order_confirmation(order):
    """Envía email de confirmación de pedido."""
    return send_email(
        subject=f"Confirmación de pedido #{order.id} - Marroquinería Artesanal",
        recipients=[order.customer_email],
        template="emails/order_confirmation.html",
        order=order,
    )


def send_welcome_email(user):
    """Envía email de bienvenida al registrarse."""
    return send_email(
        subject="¡Bienvenido/a a Marroquinería Artesanal!",
        recipients=[user.email],
        template="emails/welcome.html",
        user=user,
    )


def send_order_status_update(order, old_status: str, new_status: str):
    """Envía email al cliente cuando cambia el estado del pedido."""
    return send_email(
        subject=f"Actualización de tu pedido #{order.id} - {order.status_display}",
        recipients=[order.customer_email],
        template="emails/order_status_update.html",
        order=order,
        old_status=old_status,
        new_status=new_status,
    )


def send_contact_email(name: str, email: str, subject: str, message: str):
    """Envía el mensaje del formulario de contacto al admin."""
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
    """Notifica al usuario que su reseña fue aprobada."""
    return send_email(
        subject=f"⭐ Tu reseña fue publicada - {review.product.name}",
        recipients=[review.user.email],
        template="emails/review_approved.html",
        review=review,
    )