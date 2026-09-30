from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.repositories import (
    InboxRepository,
    MessageAlreadyProcessed,
    OrderAlreadyExists,
    OrderRepository,
    OutboxDestination,
    OutboxMessage,
    OutboxRepository,
)
from src.domain.entities import Order, OrderStatus
from src.infrastructure.persistence.models import InboxModel, OrderModel, OutboxModel


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> None:
        self._session.add(_to_model(order))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise OrderAlreadyExists(order.idempotency_key) from e

    async def get_by_id(
        self, order_id: UUID, *, for_update: bool = False
    ) -> Order | None:
        model = await self._session.get(
            OrderModel, order_id, with_for_update=for_update
        )
        return _to_entity(model) if model else None

    async def get_by_idempotency_key(self, key: str) -> Order | None:
        model = await self._session.scalar(
            select(OrderModel).where(OrderModel.idempotency_key == key)
        )
        return _to_entity(model) if model else None

    async def update(self, order: Order) -> None:
        await self._session.merge(_to_model(order))


class SQLAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: OutboxMessage) -> None:
        self._session.add(
            OutboxModel(
                id=message.id,
                destination=message.destination,
                key=message.key,
                payload=message.payload,
                created_at=datetime.now(UTC),
            )
        )

    async def get_pending(
        self, destination: OutboxDestination, limit: int
    ) -> list[OutboxMessage]:
        models = await self._session.scalars(
            select(OutboxModel)
            .where(
                OutboxModel.destination == destination,
                OutboxModel.sent_at.is_(None),
            )
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return [
            OutboxMessage(
                id=model.id,
                destination=OutboxDestination(model.destination),
                key=model.key,
                payload=model.payload,
            )
            for model in models
        ]

    async def mark_sent(self, message_ids: list[UUID]) -> None:
        await self._session.execute(
            update(OutboxModel)
            .where(OutboxModel.id.in_(message_ids))
            .values(sent_at=datetime.now(UTC))
        )


class SQLAlchemyInboxRepository(InboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message_id: str, payload: dict[str, Any]) -> None:
        self._session.add(
            InboxModel(
                message_id=message_id,
                payload=payload,
                processed_at=datetime.now(UTC),
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise MessageAlreadyProcessed(message_id) from e


def _to_model(order: Order) -> OrderModel:
    return OrderModel(
        id=order.id,
        user_id=order.user_id,
        item_id=order.item_id,
        quantity=order.quantity,
        idempotency_key=order.idempotency_key,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _to_entity(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        user_id=model.user_id,
        item_id=model.item_id,
        quantity=model.quantity,
        idempotency_key=model.idempotency_key,
        status=OrderStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
