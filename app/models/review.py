from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    # Calificación de 1 a 5 estrellas
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Comentario (opcional)
    comment: Mapped[str | None] = mapped_column(Text)
    
    # Estado de aprobación (moderación)
    approved: Mapped[bool] = mapped_column(default=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="reviews")
    product: Mapped["Product"] = relationship(back_populates="reviews")

    def __repr__(self):
        return f"<Review {self.rating}⭐ by {self.user.email} for {self.product.name}>"