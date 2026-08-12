from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, FloatField, IntegerField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from ..models import Category


class ProductForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=150)])
    slug = StringField('Slug (URL)', validators=[Optional(), Length(max=180)])
    description = TextAreaField('Descripción completa', validators=[DataRequired()])
    short_description = StringField('Descripción corta', validators=[Optional(), Length(max=255)])
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    compare_at_price = FloatField('Precio anterior (opcional)', validators=[Optional(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    sku = StringField('SKU', validators=[DataRequired(), Length(max=50)])
    artisan_name = StringField('Nombre del artesano', validators=[Optional(), Length(max=100)])
    category_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    is_handmade = BooleanField('Hecho a mano', default=True)
    featured = BooleanField('Destacado', default=False)
    active = BooleanField('Activo', default=True)
    image = FileField('Imagen del producto')
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]


class CategoryForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=80)])
    slug = StringField('Slug (URL)', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional()])
    active = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')