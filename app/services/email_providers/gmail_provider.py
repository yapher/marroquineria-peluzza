# app/services/email_providers/gmail_provider.py
"""
Provider de email vía Gmail SMTP (Flask-Mail).
Se usa en desarrollo local donde Gmail está configurado.
"""


def send(subject: str, recipients: list[str], html_content: str) -> bool:
    """
    Envía un email usando Gmail SMTP (Flask-Mail / TLS).
    Devuelve True si se envió correctamente, False si falló.
    Nunca lanza excepciones.
    """
    try:
        from flask_mail import Message
        from flask import current_app
        from ...extensions import mail

        msg = Message(subject=subject, recipients=recipients)
        msg.html = html_content
        mail.send(msg)

        print(f"   ✅ [GMAIL] Email enviado a: {recipients}")
        return True

    except Exception as e:
        print(f"   ❌ [GMAIL] Error enviando: {e}")
        try:
            from flask import current_app
            current_app.logger.error(f"[GMAIL] Error: {e}")
        except Exception:
            pass
        return False