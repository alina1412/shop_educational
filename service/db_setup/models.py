import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"),
        nullable=True,
        server_default="null",
    )


class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="RESTRICT"), nullable=False
    )


class Client(Base):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[str] = mapped_column(String(120), nullable=True)


class Order(Base):
    __tablename__ = "order"
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.id", ondelete="RESTRICT"), nullable=False
    )
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class OrderItem(Base):
    __tablename__ = "order_item"
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, server_default="1")
    price_at_time: Mapped[int] = mapped_column(Integer, nullable=False)

    # order = relationship("Order", back_populates="items")
    # product = relationship("Product", back_populates="order_items")
