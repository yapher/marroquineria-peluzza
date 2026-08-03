from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, IntegerField, BooleanField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class CouponForm(FlaskForm):
    code = StringField('Código', validators=[DataRequired(), Length(max=50)])
    discount_type = SelectField('Tipo de descuento', choices=[
        ('percentage', 'Porcentaje (%)'),
        ('fixed', 'Monto fijo ($)')
    ], validators=[DataRequired()])
    discount_value = FloatField('Valor del descuento', validators=[DataRequired(), NumberRange(min=0)])
    
    min_purchase = FloatField('Compra mínima', validators=[Optional(), NumberRange(min=0)], default=0)
    max_uses = IntegerField('Máximo de usos (0 = ilimitado)', validators=[Optional(), NumberRange(min=0)], default=0)
    
    valid_until = DateField('Válido hasta', validators=[Optional()], format='%Y-%m-%d')
    
    description = TextAreaField('Descripción (opcional)', validators=[Optional(), Length(max=255)])
    active = BooleanField('Activo', default=True)
    
    submit = SubmitField('Guardar')