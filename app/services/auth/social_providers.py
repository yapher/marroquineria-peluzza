# app/services/auth/social_providers.py
"""
Definición declarativa de los providers OAuth soportados.

Agregar un provider nuevo = 3 pasos:
1. Sumar una entrada en SOCIAL_PROVIDERS.
2. Sumar sus credenciales en .env / config.py (PROVIDER_CLIENT_ID / _SECRET).
3. Agregar su botón en templates/auth/partials/social_buttons.html.
"""

SOCIAL_PROVIDERS = {
    "google": {
        # OpenID Connect: los endpoints se descubren solos con esta URL
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
        # Google devuelve el perfil dentro del token (OIDC)
        "profile_source": "userinfo",
    },
    "facebook": {
        "authorize_url": "https://www.facebook.com/dialog/oauth",
        "access_token_url": "https://graph.facebook.com/oauth/access_token",
        "api_base_url": "https://graph.facebook.com/",
        "client_kwargs": {"scope": "email public_profile"},
        # Facebook requiere consultar su Graph API para obtener el perfil
        "profile_source": "api",
        "profile_api_path": "me?fields=id,name,email,first_name,last_name,picture.type(large)",
    },
}

# Metadatos de presentación (labels y colores de marca para la UI)
PROVIDER_META = {
    "google": {"label": "Google", "color": "#EA4335"},
    "facebook": {"label": "Facebook", "color": "#1877F2"},
}


def is_configured(provider: str, config) -> bool:
    """Verifica si un provider tiene sus credenciales configuradas."""
    return bool(
        config.get(f"{provider.upper()}_CLIENT_ID")
        and config.get(f"{provider.upper()}_CLIENT_SECRET")
    )