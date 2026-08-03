from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # ✅ RELACIÓN INVERSA CON USER (¡Esta es la que faltaba o estaba mal!)
    user: Mapped["User"] = relationship(back_populates="orders")
    
    # Datos del cliente
    customer_email: Mapped[str] = mapped_column(String(120))
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_phone: Mapped[str | None] = mapped_column(String(20))
    
    # Dirección de envío
    shipping_address: Mapped[str] = mapped_column(Text)
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_state: Mapped[str | None] = mapped_column(String(100))
    shipping_zip: Mapped[str] = mapped_column(String(20))
    shipping_country: Mapped[str] = mapped_column(String(100), default="Argentina")
    
    # Montos
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    # Cupón aplicado
    coupon_code: Mapped[str | None] = mapped_column(String(50))
    coupon_discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Cupón aplicado
    coupon_code: Mapped[str | None] = mapped_column(String(50))
    coupon_discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    level_discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, server_default='0')

    # Estado y pago
    status: Mapped[str] = mapped_column(String(30), default="pending")
    payment_method: Mapped[str | None] = mapped_column(String(50))
    payment_id: Mapped[str | None] = mapped_column(String(200))
    payment_status: Mapped[str | None] = mapped_column(String(50))
    
    # Notas
    notes: Mapped[str | None] = mapped_column(Text)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    @property
    def status_display(self) -> str:
        status_map = {
            "pending_payment": "Pago Pendiente",
            "pending": "Pendiente",
            "paid": "Pagado",
            "preparing": "En Preparación",
            "shipped": "Enviado",
            "delivered": "Entregado",
            "completed": "Completado",
            "cancelled": "Cancelado"
        }
        return status_map.get(self.status, self.status)

    @property
    def status_color(self) -> str:
        color_map = {
            "pending_payment": "yellow",
            "pending": "yellow",
            "paid": "blue",
            "preparing": "purple",
            "shipped": "indigo",
            "delivered": "green",
            "completed": "green",
            "cancelled": "red"
        }
        return color_map.get(self.status, "gray")

    @property
    def status_icon(self) -> str:
        icon_map = {
            "pending_payment": "💳",
            "pending": "⏳",
            "paid": "✅",
            "preparing": "📦",
            "shipped": "🚚",
            "delivered": "🏠",
            "completed": "🎉",
            "cancelled": "❌"
        }
        return icon_map.get(self.status, "📋")

    @property
    def next_statuses(self) -> list:
        flow = {
            "pending_payment": ["paid", "cancelled"],
            "pending": ["paid", "cancelled"],
            "paid": ["preparing", "cancelled"],
            "preparing": ["shipped", "cancelled"],
            "shipped": ["delivered"],
            "delivered": ["completed"],
            "completed": [],
            "cancelled": []
        }
        return flow.get(self.status, [])


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    
    product_name: Mapped[str] = mapped_column(String(200))
    product_sku: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity