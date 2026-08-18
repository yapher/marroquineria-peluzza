# app/models/loyalty_transaction.py
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from ..utils.time import utc_now


class LoyaltyTransaction(db.Model):
    __tablename__ = "loyalty_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Puntos (positivo = ganados, negativo = gastados)
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    # Razón de la transacción
    reason: Mapped[str] = mapped_column(String(200), nullable=False)

    # Order asociada (opcional)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)

    # Balance después de la transacción
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="loyalty_transactions")
    order: Mapped["Order"] = relationship()

    def __repr__(self):
        return f"<LoyaltyTransaction {self.points} points for user {self.user_id}>"