# app/forms/account_forms.py
"""Formularios de la cuenta de usuario."""
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        'Contraseña actual',
        validators=[DataRequired(message="Ingresa tu contraseña actual")]
    )
    new_password = PasswordField(
        'Nueva contraseña',
        validators=[
            DataRequired(),
            Length(min=6, message='La nueva contraseña debe tener al menos 6 caracteres'),
        ]
    )
    confirm_password = PasswordField(
        'Confirmar nueva contraseña',
        validators=[
            DataRequired(),
            EqualTo('new_password', message='Las contraseñas nuevas no coinciden'),
        ]
    )
    submit = SubmitField('Actualizar Contraseña')

    def validate_current_password(self, field):
        """Verifica que la contraseña actual sea correcta."""
        if not current_user.check_password(field.data):
            raise ValidationError('La contraseña actual es incorrecta')

    def validate_new_password(self, field):
        """La nueva contraseña debe ser diferente a la actual."""
        if self.current_password.data and field.data == self.current_password.data:
            raise ValidationError('La nueva contraseña debe ser diferente a la actual')