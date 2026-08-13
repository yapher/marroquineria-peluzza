# app/services/email_providers/resend_provider.py
"""
Provider de email vía Resend (API HTTP).
Se usa en producción (Render).

⚠️  Mientras el dominio no esté verificado en Resend, SOLO se puede
enviar al email de la cuenta de Resend (RESEND_SANDBOX_EMAIL).
A cualquier otro destinatario se omite el envío sin romper el flujo.
"""
import os

# Mientras no tengas dominio verificado en Resend, esta es la única
# dirección a la que Resend te deja mandar.
RESEND_SANDBOX_EMAIL = os.getenv(
    "MAIL_USERNAME", "marroquineriapeluzza@gmail.com"
).lower()


def send(subject: str, recipients: list[str], html_content: str) -> bool:
    """
    Envía un email vía Resend API.
    Filtra automáticamente los destinatarios que Resend rechazaría
    por estar en modo sandbox (dominio no verificado).
    Devuelve True si se envió correctamente, False si falló.
    Nunca lanza excepciones.
    """
    try:
        import resend

        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return False

        resend.api_key = api_key

        # Sin dominio verificado, Resend rechaza cualquier "from" que
        # no sea @resend.dev, y solo entrega a RESEND_SANDBOX_EMAIL.
        sender = "Marroquinería Artesanal <onboarding@resend.dev>"

        allowed = [r for r in recipients if r.strip().lower() == RESEND_SANDBOX_EMAIL]
        blocked = [r for r in recipients if r.strip().lower() != RESEND_SANDBOX_EMAIL]

        if blocked:
            print(
                f"   ⚠️  [RESEND] Modo sandbox: se omite el envío a {blocked} "
                f"(solo se puede mandar a {RESEND_SANDBOX_EMAIL} hasta verificar un dominio)"
            )

        if not allowed:
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