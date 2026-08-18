# app/models/product.py
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from slugify import slugify
from ..extensions import db
from ..utils.time import utc_now


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    description: Mapped[str] = mapped_column(Text)
    short_description: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    artisan_name: Mapped[str | None] = mapped_column(String(100))
    is_handmade: Mapped[bool] = mapped_column(Boolean, default=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="products")

    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    # Relación con reseñas
    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    @property
    def average_rating(self) -> float:
        """Calcula el promedio de calificaciones del producto."""
        from .review import Review
        approved_reviews = Review.query.filter_by(product_id=self.id, approved=True).all()
        if not approved_reviews:
            return 0.0
        total = sum(review.rating for review in approved_reviews)
        return round(total / len(approved_reviews), 1)

    @property
    def review_count(self) -> int:
        """Cantidad de reseñas aprobadas."""
        from .review import Review
        return Review.query.filter_by(product_id=self.id, approved=True).count()

    def has_user_reviewed(self, user_id: int) -> bool:
        """Verifica si un usuario ya reseñó este producto."""
        from .review import Review
        return Review.query.filter_by(user_id=user_id, product_id=self.id).first() is not None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)

    @property
    def main_image(self) -> str | None:
        return next((i.url for i in self.images if i.is_primary), None)

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def discount_percent(self) -> int:
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(100 - (self.price / self.compare_at_price) * 100)
        return 0


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500))
    alt: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product: Mapped["Product"] = relationship(back_populates="images")


class ProductVariant(db.Model):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    color: Mapped[str | None] = mapped_column(String(50))
    size: Mapped[str | None] = mapped_column(String(50))
    price_adjustment: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product: Mapped["Product"] = relationship(back_populates="variants")