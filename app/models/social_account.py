# app/models/social_account.py
"""Vincula un usuario local con una cuenta de un provider OAuth."""
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from ..utils.time import utc_now


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 'google', 'facebook', ...
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    # ID del usuario en el provider externo
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relación inversa con User
    user: Mapped["User"] = relationship(back_populates="social_accounts")

    # Un provider+usuario externo solo puede existir una vez
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    def __repr__(self) -> str:
        return f"<SocialAccount {self.provider}:{self.provider_user_id}>"