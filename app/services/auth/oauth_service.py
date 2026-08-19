# app/services/auth/oauth_service.py
"""
Servicio de autenticación OAuth (login social).
Orquesta el flujo de autorización con providers externos
y la creación/login de usuarios locales.
"""
import secrets

from flask import current_app
from authlib.integrations.base_client import OAuthError

from ...extensions import oauth, db
from ...models import User, SocialAccount
from .social_providers import SOCIAL_PROVIDERS, PROVIDER_META, is_configured


# ============================================
# CONSULTAS DE ESTADO
# ============================================
def is_known_provider(provider: str) -> bool:
    return provider in SOCIAL_PROVIDERS


def is_provider_enabled(provider: str) -> bool:
    if not is_known_provider(provider):
        return False
    return is_configured(provider, current_app.config)


def get_enabled_providers() -> list[dict]:
    return [
        {
            "key": key,
            "label": PROVIDER_META[key]["label"],
            "color": PROVIDER_META[key]["color"],
        }
        for key in SOCIAL_PROVIDERS
        if is_configured(key, current_app.config)
    ]


# ============================================
# REGISTRO EN LA APP
# ============================================
def register_providers(app) -> None:
    for key, spec in SOCIAL_PROVIDERS.items():
        if not is_configured(key, app.config):
            app.logger.warning(f"⚠️ Provider OAuth NO registrado (faltan credenciales): {key}")
            continue
        registration = {
            "client_id": app.config[f"{key.upper()}_CLIENT_ID"],
            "client_secret": app.config[f"{key.upper()}_CLIENT_SECRET"],
            "client_kwargs": spec.get("client_kwargs", {}),
        }
        if "server_metadata_url" in spec:
            registration["server_metadata_url"] = spec["server_metadata_url"]
        for field in ("authorize_url", "access_token_url", "api_base_url"):
            if field in spec:
                registration[field] = spec[field]
        oauth.register(name=key, **registration)
        app.logger.info(f"🔐 Provider OAuth registrado: {key}")


# ============================================
# FLUJO OAUTH
# ============================================
def get_redirect_uri(provider: str) -> str:
    base = current_app.config.get("PUBLIC_URL", "http://localhost:5000").rstrip("/")
    return f"{base}/auth/callback/{provider}"


def start_oauth_flow(provider: str):
    client = oauth.create_client(provider)
    if client is None:
        current_app.logger.error(f"❌ oauth.create_client('{provider}') devolvió None. Provider no registrado.")
        return None
    return client.authorize_redirect(get_redirect_uri(provider))


def extract_profile(provider: str, token: dict) -> dict | None:
    spec = SOCIAL_PROVIDERS[provider]
    if spec.get("profile_source") == "userinfo":
        return token.get("userinfo")
    client = oauth.create_client(provider)
    if client is None:
        return None
    resp = client.get(spec["profile_api_path"], token=token)
    if resp.status_code != 200:
        return None
    return resp.json()


def complete_oauth_flow(provider: str) -> tuple:
    client = oauth.create_client(provider)
    if client is None:
        current_app.logger.error(f"❌ oauth.create_client('{provider}') devolvió None en callback.")
        return None, "Proveedor no disponible."
    try:
        token = client.authorize_access_token()
        profile = extract_profile(provider, token)
        if not profile:
            return None, "No se pudo obtener el perfil del proveedor."
        user = get_or_create_user(provider, profile)
        return user, None
    except OAuthError as e:
        current_app.logger.error(f"❌ OAuthError ({provider}): {e.error} - {e.description}")
        if current_app.debug:
            return None, f"OAuthError: {e.error} - {e.description}"
        return None, "No se pudo completar el inicio de sesión. Intentá de nuevo."
    except Exception as e:
        current_app.logger.error(f"❌ Error en OAuth ({provider}): {e}", exc_info=True)
        if current_app.debug:
            return None, f"Error: {type(e).__name__}: {e}"
        return None, "No se pudo completar el inicio de sesión. Intentá de nuevo."


# ============================================
# CREACIÓN / VINCULACIÓN DE USUARIOS
# ============================================
def get_or_create_user(provider: str, profile: dict) -> User:
    provider_user_id = str(profile.get("id") or profile.get("sub"))
    email = (profile.get("email") or "").lower().strip()

    social = SocialAccount.query.filter_by(
        provider=provider, provider_user_id=provider_user_id
    ).first()
    if social:
        return social.user

    user = None
    if email:
        user = User.query.filter_by(email=email).first()

    if user is None:
        if not email:
            raise ValueError(f"El provider '{provider}' no devolvió un email.")
        first_name = _extract_first_name(profile) or email.split("@")[0]
        last_name = _extract_last_name(profile) or "Usuario"
        user = User(email=email, first_name=first_name, last_name=last_name)
        user.set_password(secrets.token_urlsafe(24))
        db.session.add(user)
        db.session.flush()

    db.session.add(SocialAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=email or None,
    ))
    db.session.commit()
    return user


def _extract_first_name(profile: dict) -> str:
    if profile.get("first_name"):
        return profile["first_name"]
    if profile.get("given_name"):
        return profile["given_name"]
    if profile.get("name"):
        return profile["name"].split(" ", 1)[0]
    return ""


def _extract_last_name(profile: dict) -> str:
    if profile.get("last_name"):
        return profile["last_name"]
    if profile.get("family_name"):
        return profile["family_name"]
    if profile.get("name") and " " in profile["name"]:
        return profile["name"].split(" ", 1)[1]
    return ""