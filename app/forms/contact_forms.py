# app/forms/contact_forms.py
"""Formulario de contacto (reemplaza la validación manual con regex)."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    name = StringField(
        'Nombre completo',
        validators=[DataRequired(message="El nombre es obligatorio"), Length(max=100)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(message="El email es obligatorio"), Email(message="Ingresa un email válido")]
    )
    subject = StringField(
        'Asunto',
        validators=[Optional(), Length(max=150)]
    )
    message = TextAreaField(
        'Mensaje',
        validators=[DataRequired(message="El mensaje es obligatorio"), Length(max=2000)]
    )
    submit = SubmitField('Enviar Mensaje')