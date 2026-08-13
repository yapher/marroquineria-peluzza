# app/models/user.py
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric
from ..config.constants import (
    LOYALTY_LEVELS,
    LoyaltyLevel,
    REVIEWABLE_ORDER_STATUSES,
    get_next_loyalty_level,
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Sistema de fidelización
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0)
    loyalty_level: Mapped[str] = mapped_column(String(20), default=LoyaltyLevel.BRONZE)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # ==========================================
    # RELACIONES
    # ==========================================
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    wishlist_items: Mapped[list["Wishlist"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    loyalty_transactions: Mapped[list["LoyaltyTransaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(LoyaltyTransaction.created_at)"
    )

    # ==========================================
    # MÉTODOS Y PROPIEDADES
    # ==========================================
    @property
    def full_name(self) -> str:
        """Devuelve el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password: str):
        """Hashea y guarda la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña es correcta."""
        return check_password_hash(self.password_hash, password)

    def is_in_wishlist(self, product_id: int) -> bool:
        """Verifica si un producto está en la wishlist del usuario."""
        from .wishlist import Wishlist
        return Wishlist.query.filter_by(
            user_id=self.id,
            product_id=product_id
        ).first() is not None

    @property
    def wishlist_count(self) -> int:
        """Cantidad de productos en la wishlist del usuario."""
        from .wishlist import Wishlist
        return Wishlist.query.filter_by(user_id=self.id).count()

    def has_purchased_product(self, product_id: int) -> bool:
        """Verifica si el usuario compró un producto específico."""
        from .order import Order, OrderItem
        purchased = OrderItem.query.join(Order).filter(
            Order.user_id == self.id,
            Order.status.in_(REVIEWABLE_ORDER_STATUSES),
            OrderItem.product_id == product_id
        ).first()
        return purchased is not None

    # ==========================================
    # SISTEMA DE FIDELIZACIÓN
    # ==========================================
    @property
    def loyalty_level_display(self) -> str:
        """Nombre del nivel en español."""
        return LOYALTY_LEVELS.get(self.loyalty_level, LOYALTY_LEVELS[LoyaltyLevel.BRONZE])["name"]

    @property
    def loyalty_discount(self) -> float:
        """Descuento porcentual según el nivel."""
        return LOYALTY_LEVELS.get(self.loyalty_level, {}).get("discount", 0)

    @property
    def next_level(self) -> dict:
        """Información del siguiente nivel."""
        return get_next_loyalty_level(self.loyalty_level)

    @property
    def points_to_next_level(self) -> int:
        """Puntos faltantes para el siguiente nivel."""
        next_level = self.next_level
        if next_level["points"] is None:
            return 0
        return max(0, next_level["points"] - self.loyalty_points)

    @property
    def level_progress(self) -> float:
        """Progreso hacia el siguiente nivel (0-100%)."""
        next_level = self.next_level
        if next_level["points"] is None:
            return 100.0

        current_threshold = LOYALTY_LEVELS.get(self.loyalty_level, {}).get("threshold", 0)
        range_size = next_level["points"] - current_threshold
        if range_size == 0:
            return 100.0

        progress = ((self.loyalty_points - current_threshold) / range_size) * 100
        return min(100.0, max(0.0, progress))

    def add_points(self, points: int, reason: str, order_id: int = None):
        """Agrega puntos al usuario y registra la transacción."""
        from .loyalty_transaction import LoyaltyTransaction
        from ..extensions import db

        self.loyalty_points += points

        # Verificar si subió de nivel (solo sube, nunca baja → mismo comportamiento original)
        old_level = self.loyalty_level
        if self.loyalty_points >= LOYALTY_LEVELS[LoyaltyLevel.PLATINUM]["threshold"]:
            self.loyalty_level = LoyaltyLevel.PLATINUM
        elif self.loyalty_points >= LOYALTY_LEVELS[LoyaltyLevel.GOLD]["threshold"]:
            self.loyalty_level = LoyaltyLevel.GOLD
        elif self.loyalty_points >= LOYALTY_LEVELS[LoyaltyLevel.SILVER]["threshold"]:
            self.loyalty_level = LoyaltyLevel.SILVER

        # Registrar transacción
        transaction = LoyaltyTransaction(
            user_id=self.id,
            points=points,
            reason=reason,
            order_id=order_id,
            balance_after=self.loyalty_points
        )
        db.session.add(transaction)

        return old_level != self.loyalty_level  # Retorna True si subió de nivel