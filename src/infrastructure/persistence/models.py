from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[str]
    item_id: Mapped[str]
    quantity: Mapped[int]
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OutboxModel(Base):
    __tablename__ = "outbox"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    destination: Mapped[str]
    key: Mapped[str]
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InboxModel(Base):
    __tablename__ = "inbox"

    message_id: Mapped[str] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
