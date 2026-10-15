from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Enum as SqlEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="check_positive_stock"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name='{self.name}' stock={self.stock_quantity}>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(
        SqlEnum(OrderStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrderStatus.DRAFT,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_item_quantity"),
    )

    order = relationship("Order", back_populates="items")
    product = relationship("Product", lazy="selectin")

    @property
    def product_name(self) -> str | None:
        return self.product.name if self.product else None

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} product_id={self.product_id} qty={self.quantity}>"
