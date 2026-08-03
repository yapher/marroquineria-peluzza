"""
Servicio de emails usando Resend API (HTTP, no SMTP).
Funciona en Render porque usa HTTPS en lugar de SMTP.
"""
import os
import resend
from flask import current_app, render_template


def send_email_resend(subject: str, recipients: list[str], template: str, **context):
    """
    Envía email usando Resend API (no bloquea el worker, no requiere SMTP).
    """
    try:
        print(f"\n📧 [RESEND] Intentando enviar email...")
        print(f"   Para: {recipients}")
        print(f"   Asunto: {subject}")
        
        # Configurar API key
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print("   ❌ RESEND_API_KEY no está configurada")
            return False
        
        resend.api_key = api_key
        
        # Limpiar destinatarios
        cleaned_recipients = []
        for r in recipients:
            if '<' in r and '>' in r:
                email_only = r.split('<')[1].split('>')[0]
                cleaned_recipients.append(email_only)
            else:
                cleaned_recipients.append(r)
        
        # Renderizar plantilla HTML
        html_content = render_template(template, **context)
        
        # Email remitente
        sender = os.getenv("MAIL_DEFAULT_SENDER", "Marroquinería Peluzza <onboarding@resend.dev>")
        # Si el sender tiene formato "Nombre <email>", extraer solo email para validar
        if '<' in sender:
            sender_email = sender.split('<')[1].split('>')[0]
            # Usar formato completo solo si es un dominio verificado
            # Si es @resend.dev, usarlo tal cual
            if sender_email.endswith('@resend.dev'):
                final_sender = sender
            else:
                final_sender = f"Marroquinería Peluzza <{sender_email}>"
        else:
            final_sender = f"Marroquinería Peluzza <{sender}>"
        
        # Enviar usando la API de Resend (HTTP, no SMTP)
        response = resend.Emails.send({
            "from": final_sender,
            "to": cleaned_recipients,
            "subject": subject,
            "html": html_content,
        })
        
        print(f"   ✅ ¡EMAIL ENVIADO CON ÉXITO! ID: {response.get('id', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"\n   ❌ ERROR enviando con Resend: {e}")
        print(f"   💡 Verifica que RESEND_API_KEY sea correcta y el dominio esté verificado")
        return False


def send_order_confirmation(order):
    return send_email_resend(
        subject=f"Confirmación de pedido #{order.id} - Marroquinería Artesanal",
        recipients=[order.customer_email],
        template="emails/order_confirmation.html",
        order=order,
    )


def send_welcome_email(user):
    return send_email_resend(
        subject="¡Bienvenido/a a Marroquinería Artesanal!",
        recipients=[user.email],
        template="emails/welcome.html",
        user=user,
    )


def send_order_status_update(order, old_status: str, new_status: str):
    return send_email_resend(
        subject=f"Actualización de tu pedido #{order.id} - {order.status_display}",
        recipients=[order.customer_email],
        template="emails/order_status_update.html",
        order=order,
        old_status=old_status,
        new_status=new_status,
    )


def send_contact_email(name: str, email: str, subject: str, message: str):
    admin_email = current_app.config.get('MAIL_USERNAME', 'marroquineriapeluzza@gmail.com')
    return send_email_resend(
        subject=f"📬 Nuevo mensaje de contacto: {subject or 'Sin asunto'}",
        recipients=[admin_email],
        template="emails/contact_notification.html",
        name=name,
        email=email,
        contact_subject=subject,
        message=message,
    )


def send_review_approved(review):
    return send_email_resend(
        subject=f"⭐ Tu reseña fue publicada - {review.product.name}",
        recipients=[review.user.email],
        template="emails/review_approved.html",
        review=review,
    )