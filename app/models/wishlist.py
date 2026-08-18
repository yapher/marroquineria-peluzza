# app/models/wishlist.py
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from ..utils.time import utc_now


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # ✅ RELACIONES
    user: Mapped["User"] = relationship(back_populates="wishlist_items")
    product: Mapped["Product"] = relationship()

    # Un usuario no puede tener el mismo producto dos veces en su wishlist
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_wishlist'),
    )