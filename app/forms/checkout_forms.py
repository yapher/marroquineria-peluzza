from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class CheckoutForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Nombre completo', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    
    address = StringField('Dirección', validators=[DataRequired(), Length(max=300)])
    city = StringField('Ciudad', validators=[DataRequired(), Length(max=100)])
    state = StringField('Provincia/Estado', validators=[Optional(), Length(max=100)])
    zip_code = StringField('Código Postal', validators=[DataRequired(), Length(max=20)])
    country = StringField('País', validators=[DataRequired(), Length(max=100)])
    
    notes = TextAreaField('Notas del pedido (opcional)', validators=[Optional()])