# tests/test_social_auth.py
"""
Tests de login social (OAuth).
El flujo real con los providers se mockea: nunca salen requests de red.
"""
from unittest.mock import patch

from werkzeug.wrappers import Response

from app.models import User, SocialAccount


# ============================================
# CONFIGURACIÓN DE PROVIDERS
# ============================================
class TestSocialProvidersConfig:
    def test_no_providers_enabled_by_default(self, app, db):
        from app.services.auth.oauth_service import get_enabled_providers
        assert get_enabled_providers() == []

    def test_google_enabled_when_configured(self, app, db):
        app.config['GOOGLE_CLIENT_ID'] = 'cid'
        app.config['GOOGLE_CLIENT_SECRET'] = 'secret'
        from app.services.auth.oauth_service import get_enabled_providers
        keys = [p['key'] for p in get_enabled_providers()]
        assert 'google' in keys
        assert 'facebook' not in keys

    def test_unknown_provider_not_known(self, app, db):
        from app.services.auth.oauth_service import is_known_provider
        assert is_known_provider('twitter') is False


# ============================================
# CREACIÓN / VINCULACIÓN DE USUARIOS
# ============================================
class TestGetOrCreateUser:
    def _profile(self):
        return {
            'sub': 'g-123', 'id': 'g-123',
            'email': 'social@test.com',
            'given_name': 'Sofía', 'family_name': 'Ríos',
            'name': 'Sofía Ríos',
        }

    def test_creates_new_user(self, app, db):
        from app.services.auth.oauth_service import get_or_create_user
        user = get_or_create_user('google', self._profile())
        assert user.email == 'social@test.com'
        assert user.first_name == 'Sofía'
        assert SocialAccount.query.filter_by(provider='google').count() == 1

    def test_reuses_existing_social_account(self, app, db):
        from app.services.auth.oauth_service import get_or_create_user
        first = get_or_create_user('google', self._profile())
        second = get_or_create_user('google', self._profile())
        assert first.id == second.id
        # No duplica la cuenta social
        assert SocialAccount.query.filter_by(provider='google').count() == 1

    def test_links_to_existing_user_by_email(self, app, db, user):
        from app.services.auth.oauth_service import get_or_create_user
        profile = self._profile()
        profile['email'] = 'cliente@test.com'  # email del fixture `user`
        linked = get_or_create_user('google', profile)
        assert linked.id == user.id
        assert SocialAccount.query.filter_by(user_id=user.id).count() == 1

    def test_missing_email_raises(self, app, db):
        import pytest
        from app.services.auth.oauth_service import get_or_create_user
        profile = {'sub': 'x-1', 'name': 'Sin Email'}
        with pytest.raises(ValueError):
            get_or_create_user('google', profile)


# ============================================
# RUTAS
# ============================================
class TestSocialRoutes:
    def test_unknown_provider_404(self, client, db):
        resp = client.get('/auth/login/twitter')
        assert resp.status_code == 404

    def test_unconfigured_provider_redirects_to_login(self, client, db):
        resp = client.get('/auth/login/google', follow_redirects=True)
        assert resp.status_code == 200

    def test_social_login_starts_flow(self, client, db, app):
        app.config['GOOGLE_CLIENT_ID'] = 'cid'
        app.config['GOOGLE_CLIENT_SECRET'] = 'secret'
        with patch('app.blueprints.auth.routes.start_oauth_flow') as mock_start:
            mock_start.return_value = Response(status=302, headers={'Location': '/'})
            resp = client.get('/auth/login/google')
            mock_start.assert_called_once_with('google')
            assert resp.status_code == 302

    def test_callback_error_redirects_to_login(self, client, db):
        with patch('app.blueprints.auth.routes.complete_oauth_flow',
                   return_value=(None, 'No se pudo')):
            resp = client.get('/auth/callback/google', follow_redirects=True)
            assert resp.status_code == 200

    def test_callback_success_logs_user_in(self, client, db, user):
        with patch('app.blueprints.auth.routes.complete_oauth_flow',
                   return_value=(user, None)):
            resp = client.get('/auth/callback/google', follow_redirects=True)
            assert resp.status_code == 200
            # El usuario quedó logueado: puede entrar a su cuenta
            resp2 = client.get('/cuenta/')
            assert resp2.status_code == 200