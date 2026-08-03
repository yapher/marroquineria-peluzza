from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric

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
    loyalty_level: Mapped[str] = mapped_column(String(20), default="bronze")
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

        # Relación con transacciones de fidelización
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
            Order.status.in_(["paid", "shipped", "delivered", "completed"]),
            OrderItem.product_id == product_id
        ).first()
        
        return purchased is not None

        # ==========================================
    # SISTEMA DE FIDELIZACIÓN
    # ==========================================
    
    @property
    def loyalty_level_display(self) -> str:
        """Nombre del nivel en español."""
        levels = {
            "bronze": "Bronce 🥉",
            "silver": "Plata 🥈",
            "gold": "Oro 🥇",
            "platinum": "Platino 💎"
        }
        return levels.get(self.loyalty_level, "Bronce 🥉")
    
    @property
    def loyalty_discount(self) -> float:
        """Descuento porcentual según el nivel."""
        discounts = {
            "bronze": 0,
            "silver": 5,
            "gold": 10,
            "platinum": 15
        }
        return discounts.get(self.loyalty_level, 0)
    
    @property
    def next_level(self) -> dict:
        """Información del siguiente nivel."""
        thresholds = {
            "bronze": {"name": "Plata 🥈", "points": 1000, "discount": 5},
            "silver": {"name": "Oro 🥇", "points": 5000, "discount": 10},
            "gold": {"name": "Platino 💎", "points": 10000, "discount": 15},
            "platinum": {"name": "Máximo", "points": None, "discount": 15}
        }
        return thresholds.get(self.loyalty_level, thresholds["bronze"])
    
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
        
        # Calcular el umbral del nivel actual
        current_thresholds = {
            "bronze": 0,
            "silver": 1000,
            "gold": 5000,
            "platinum": 10000
        }
        current_threshold = current_thresholds.get(self.loyalty_level, 0)
        
        # Progreso dentro del rango del nivel actual
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
        
        # Verificar si subió de nivel
        old_level = self.loyalty_level
        if self.loyalty_points >= 10000:
            self.loyalty_level = "platinum"
        elif self.loyalty_points >= 5000:
            self.loyalty_level = "gold"
        elif self.loyalty_points >= 1000:
            self.loyalty_level = "silver"
        
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