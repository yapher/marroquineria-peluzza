import click
from flask.cli import with_appcontext
from .extensions import db
from .models import Category, Product, User


@click.command('seed')
@with_appcontext
def seed_command():
    """Puebla la base de datos con datos de prueba."""
    
    # Categorías
    cats = [
        {"name": "Billeteras", "slug": "billeteras", "description": "Billeteras de cuero genuino hechas a mano."},
        {"name": "Bolsos", "slug": "bolsos", "description": "Bolsos artesanales únicos y duraderos."},
        {"name": "Cinturones", "slug": "cinturones", "description": "Cinturones de cuero macizo con hebillas de bronce."},
    ]
    
    categories = {}
    for c in cats:
        cat = Category.query.filter_by(slug=c["slug"]).first()
        if not cat:
            cat = Category(**c)
            db.session.add(cat)
        categories[c["slug"]] = cat

    db.session.commit()

    # Productos
    products = [
        {
            "name": "Billetera Clásica Marrón",
            "slug": "billetera-clasica-marron",
            "description": "Billetera de cuero vacuno curtido al vegetal. 6 ranuras para tarjetas y compartimento para billetes.",
            "price": 45.00,
            "stock": 15,
            "sku": "BIL-001",
            "artisan_name": "Taller El Artesano",
            "featured": True,
            "category": categories["billeteras"]
        },
        {
            "name": "Bolso Tote Negro",
            "slug": "bolso-tote-negro",
            "description": "Bolso espacioso, ideal para el día a día. Cuero negro con costuras reforzadas.",
            "price": 120.00,
            "stock": 8,
            "sku": "BOL-001",
            "artisan_name": "Taller El Artesano",
            "featured": True,
            "category": categories["bolsos"]
        },
        {
            "name": "Cinturón Rústico",
            "slug": "cinturon-rustico",
            "description": "Cinturón de 4cm de ancho, cuero grueso con hebilla de bronce envejecido.",
            "price": 35.00,
            "stock": 20,
            "sku": "CIN-001",
            "artisan_name": "Taller El Artesano",
            "featured": True,
            "category": categories["cinturones"]
        }
    ]

    for p in products:
        if not Product.query.filter_by(slug=p["slug"]).first():
            prod = Product(**p)
            db.session.add(prod)

    db.session.commit()
    click.echo("✅ Base de datos poblada con productos")


@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Crea un usuario administrador."""
    email = click.prompt('Email del admin', default='admin@marroquineria.com')
    password = click.prompt('Contraseña', hide_input=True, confirmation_prompt=True)
    first_name = click.prompt('Nombre', default='Admin')
    last_name = click.prompt('Apellido', default='User')

    if User.query.filter_by(email=email).first():
        click.echo(f"❌ El usuario {email} ya existe")
        return

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_admin=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f"✅ Admin creado: {email}")