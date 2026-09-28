from uuid import UUID

from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import GetOrderPort
from src.domain.entities import Order
from src.domain.exceptions import OrderNotFound


class GetOrder(GetOrderPort):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self, order_id: UUID) -> Order:
        async with self._uow as uow:
            order = await uow.orders.get_by_id(order_id)
        if order is None:
            raise OrderNotFound(order_id)
        return order
