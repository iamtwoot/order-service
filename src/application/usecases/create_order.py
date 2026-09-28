from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import CreateOrderInput, CreateOrderPort
from src.domain.entities import Order


class CreateOrder(CreateOrderPort):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self, data: CreateOrderInput) -> Order:
        order = Order.create(
            user_id=data.user_id,
            item_id=data.item_id,
            quantity=data.quantity,
            idempotency_key=data.idempotency_key,
        )
        async with self._uow as uow:
            await uow.orders.add(order)
            await uow.commit()
        return order
