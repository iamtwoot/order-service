from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.repositories import OrderRepository
from src.domain.entities import Order, OrderStatus
from src.infrastructure.persistence.models import OrderModel


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> None:
        self._session.add(_to_model(order))

    async def get_by_id(self, order_id: UUID) -> Order | None:
        model = await self._session.get(OrderModel, order_id)
        return _to_entity(model) if model else None


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
