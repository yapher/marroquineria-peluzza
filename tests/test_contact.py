# tests/test_contact.py
"""
Tests del formulario de contacto.

⚠️ Los literales de bytes solo aceptan ASCII (b'...').
Para verificar texto con acentos se decodifica la respuesta a str.
"""
from unittest.mock import patch


def _html(response):
    """Decodifica la respuesta a texto UTF-8 para asserts con acentos."""
    return response.data.decode('utf-8')


class TestContactPage:
    """La página de contacto carga correctamente."""

    def test_contact_page_loads(self, client):
        response = client.get('/contacto')
        assert response.status_code == 200

    def test_contact_page_contains_form(self, client):
        response = client.get('/contacto')
        assert 'Envíanos un mensaje' in _html(response)


class TestContactValidation:
    """Validación de campos obligatorios."""

    @patch('app.blueprints.main.routes.send_contact_email')
    def test_missing_name_shows_error(self, mock_send, client):
        response = client.post('/contacto', data={
            'email': 'test@test.com',
            'subject': 'Consulta',
            'message': 'Hola, quiero información',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'obligatorio' in _html(response)
        mock_send.assert_not_called()

    @patch('app.blueprints.main.routes.send_contact_email')
    def test_invalid_email_shows_error(self, mock_send, client):
        response = client.post('/contacto', data={
            'name': 'Juan Pérez',
            'email': 'no-es-un-email',
            'message': 'Hola',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'email' in _html(response).lower()
        mock_send.assert_not_called()

    @patch('app.blueprints.main.routes.send_contact_email')
    def test_missing_message_shows_error(self, mock_send, client):
        response = client.post('/contacto', data={
            'name': 'Juan Pérez',
            'email': 'test@test.com',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'obligatorio' in _html(response)
        mock_send.assert_not_called()


class TestContactSubmission:
    """Envío del formulario (email mockeado, nunca sale de la máquina)."""

    @patch('app.blueprints.main.routes.send_contact_email')
    def test_valid_submission_sends_email(self, mock_send, client):
        mock_send.return_value = True
        response = client.post('/contacto', data={
            'name': 'Juan Pérez',
            'email': 'juan@test.com',
            'subject': 'Consulta sobre producto',
            'message': 'Hola, quisiera saber más sobre los materiales.',
        }, follow_redirects=True)
        assert response.status_code == 200
        mock_send.assert_called_once()
        assert 'Mensaje enviado' in _html(response)

    @patch('app.blueprints.main.routes.send_contact_email')
    def test_email_failure_shows_error(self, mock_send, client):
        mock_send.side_effect = Exception('SMTP caído')
        response = client.post('/contacto', data={
            'name': 'Juan Pérez',
            'email': 'juan@test.com',
            'message': 'Hola',
        }, follow_redirects=True)
        assert response.status_code == 200
        mock_send.assert_called_once()
        assert 'error' in _html(response).lower()