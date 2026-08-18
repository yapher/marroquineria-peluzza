# app/models/coupon.py
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Boolean, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column
from ..extensions import db
from ..utils.time import utc_now


class Coupon(db.Model):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Tipo de descuento
    discount_type: Mapped[str] = mapped_column(String(20))  # 'percentage' o 'fixed'
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # % o monto fijo

    # Restricciones
    min_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    max_uses: Mapped[int] = mapped_column(Integer, default=0)  # 0 = ilimitado
    uses_count: Mapped[int] = mapped_column(Integer, default=0)

    # Fechas de validez
    valid_from: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Estado
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Descripción (opcional)
    description: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    @property
    def is_valid(self) -> bool:
        """Verifica si el cupón es válido actualmente."""
        if not self.active:
            return False

        now = utc_now()

        if self.valid_until and now > self.valid_until:
            return False

        if self.max_uses > 0 and self.uses_count >= self.max_uses:
            return False

        return True

    @property
    def discount_display(self) -> str:
        """Muestra el descuento de forma legible."""
        if self.discount_type == 'percentage':
            val = float(self.discount_value)
            if val.is_integer():
                return f"{int(val)}%"
            return f"{val}%"
        else:
            return f"${self.discount_value}"

    def apply_discount(self, subtotal: Decimal) -> Decimal:
        """Calcula el monto del descuento."""
        if subtotal < self.min_purchase:
            return Decimal("0")

        if self.discount_type == 'percentage':
            discount = subtotal * (self.discount_value / Decimal("100"))
        else:
            discount = self.discount_value

        # El descuento no puede ser mayor al subtotal
        return min(discount, subtotal)