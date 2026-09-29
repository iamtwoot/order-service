from src.application.ports.clients import CatalogClient
from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import CreateOrderInput, CreateOrderPort
from src.domain.entities import Order
from src.domain.exceptions import InsufficientStock, ItemNotFound


class CreateOrder(CreateOrderPort):
    def __init__(self, uow: UnitOfWork, catalog: CatalogClient) -> None:
        self._uow = uow
        self._catalog = catalog

    async def __call__(self, data: CreateOrderInput) -> Order:
        item = await self._catalog.get_item(data.item_id)
        if item is None:
            raise ItemNotFound(data.item_id)
        if item.available_qty < data.quantity:
            raise InsufficientStock(data.item_id)

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
