# tests/conftest.py
"""
Fixtures compartidos para TODOS los tests (versión unificada).

- Tests originales usan: category, product, user, admin_user, coupon,
  coupon_fixed, product_out_of_stock, auth_client, admin_client, runner.
- Tests nuevos usan: regular_user, sample_product, expensive_product,
  sample_category, session, login_user.

Este conftest provee AMBOS conjuntos para que toda la suite funcione.

⚠️ REGLA: el fixture `db` mantiene un app_context activo durante cada
test. NO hay que abrir `with app.app_context():` dentro de los tests
(hacerlo crea una segunda sesión paralela y produce errores raros).
"""
import pytest
from decimal import Decimal

from app import create_app
from app.extensions import db as _db
from app.models import User, Category, Product, Coupon


# ============================================
# APP / DB / CLIENT
# ============================================
@pytest.fixture
def app():
    """App Flask en modo testing (configuración reforzada)."""
    app = create_app('testing')
    # Refuerzos por si create_app no mapea 'testing' a TestingConfig
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['MAIL_SUPPRESS_SEND'] = True
    # Garantiza SQLite en memoria: los tests NUNCA tocan dev.db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    yield app


@pytest.fixture(scope='function')
def db(app):
    """Tablas limpias por test + app_context activo durante el test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def session(db):
    """Sesión de BD (alias para los tests nuevos)."""
    return db.session


@pytest.fixture
def client(app, db):
    """Cliente HTTP de pruebas."""
    return app.test_client()


@pytest.fixture
def runner(app, db):
    """Runner para comandos CLI."""
    return app.test_cli_runner()


# ============================================
# HELPER DE LOGIN
# (importable: from tests.conftest import login_user)
# ============================================
def login_user(client, user, password=None):
    """Inicia sesión con el usuario indicado."""
    if password is None:
        password = 'admin123' if user.is_admin else 'user123'
    return client.post('/auth/login', data={
        'email': user.email,
        'password': password,
    }, follow_redirects=True)


# ============================================
# USUARIOS
# ============================================
@pytest.fixture
def user(db):
    """Usuario cliente (tests originales). Password: password123"""
    u = User(email="cliente@test.com", first_name="Juan", last_name="Pérez")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def regular_user(db):
    """Usuario cliente (tests nuevos). Password: user123"""
    u = User(email="juan@test.com", first_name="Juan", last_name="Perez")
    u.set_password("user123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def admin_user(db):
    """Usuario administrador. Password: admin123"""
    u = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        is_admin=True,
    )
    u.set_password("admin123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_client(client, user):
    """Cliente logueado como usuario normal."""
    client.post('/auth/login', data={
        'email': 'cliente@test.com',
        'password': 'password123',
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Cliente logueado como administrador."""
    client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'admin123',
    }, follow_redirects=True)
    return client


# ============================================
# DATOS DE PRUEBA
# ============================================
@pytest.fixture
def category(db):
    """Categoría de prueba (tests originales)."""
    cat = Category(
        name="Billeteras",
        slug="billeteras",
        description="Billeteras de cuero",
        active=True,
    )
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def sample_category(db):
    """Categoría de prueba (tests nuevos)."""
    cat = Category(
        name="Billeteras Test",
        slug="billeteras-test",
        description="Categoría de tests",
        active=True,
    )
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def product(db, category):
    """Producto de prueba (tests originales). $45 / stock 10."""
    prod = Product(
        name="Billetera Clásica",
        slug="billetera-clasica",
        description="Billetera de cuero vacuno",
        short_description="Billetera clásica",
        price=Decimal("45.00"),
        stock=10,
        sku="BIL-001",
        artisan_name="Taller El Artesano",
        category_id=category.id,
        is_handmade=True,
        featured=True,
        active=True,
    )
    db.session.add(prod)
    db.session.commit()
    return prod


@pytest.fixture
def sample_product(db, sample_category):
    """Producto de prueba (tests nuevos). $50 / stock 10."""
    prod = Product(
        name="Billetera Clásica",
        slug="billetera-clasica-test",
        description="Billetera de cuero premium",
        short_description="Billetera de test",
        price=Decimal("50.00"),
        stock=10,
        sku="BIL-001-TEST",
        artisan_name="Taller El Artesano",
        category_id=sample_category.id,
        is_handmade=True,
        featured=True,
        active=True,
    )
    db.session.add(prod)
    db.session.commit()
    return prod


@pytest.fixture
def expensive_product(db, sample_category):
    """Producto de $120 para testear el envío gratis."""
    prod = Product(
        name="Bolso Premium",
        slug="bolso-premium",
        description="Bolso de cuero premium",
        short_description="Bolso caro de test",
        price=Decimal("120.00"),
        stock=5,
        sku="BOL-001-TEST",
        category_id=sample_category.id,
        active=True,
    )
    db.session.add(prod)
    db.session.commit()
    return prod


@pytest.fixture
def product_out_of_stock(db, category):
    """Producto sin stock."""
    prod = Product(
        name="Bolso Agotado",
        slug="bolso-agotado",
        description="Sin stock",
        price=Decimal("100.00"),
        stock=0,
        sku="BOL-000",
        category_id=category.id,
        active=True,
    )
    db.session.add(prod)
    db.session.commit()
    return prod


@pytest.fixture
def coupon(db):
    """Cupón TEST10: 10% de descuento, activo."""
    c = Coupon(
        code="TEST10",
        discount_type="percentage",
        discount_value=Decimal("10"),
        min_purchase=Decimal("0"),
        max_uses=0,
        active=True,
    )
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def coupon_fixed(db):
    """Cupón FIXED5: $5 fijo, compra mínima $20."""
    c = Coupon(
        code="FIXED5",
        discount_type="fixed",
        discount_value=Decimal("5.00"),
        min_purchase=Decimal("20"),
        max_uses=100,
        active=True,
    )
    db.session.add(c)
    db.session.commit()
    return c