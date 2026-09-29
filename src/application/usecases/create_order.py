from src.application.ports.clients import (
    CatalogClient,
    PaymentCreationFailed,
    PaymentsClient,
)
from src.application.ports.repositories import OrderAlreadyExists
from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import CreateOrderInput, CreateOrderPort
from src.domain.entities import Order
from src.domain.exceptions import InsufficientStock, ItemNotFound


class CreateOrder(CreateOrderPort):
    def __init__(
        self, uow: UnitOfWork, catalog: CatalogClient, payments: PaymentsClient
    ) -> None:
        self._uow = uow
        self._catalog = catalog
        self._payments = payments

    async def __call__(self, data: CreateOrderInput) -> Order:
        if existing := await self._find_by_key(data.idempotency_key):
            return existing

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
        try:
            async with self._uow as uow:
                await uow.orders.add(order)
                await uow.commit()
        except OrderAlreadyExists:
            if existing := await self._find_by_key(data.idempotency_key):
                return existing
            raise

        try:
            await self._payments.create_payment(
                order_id=order.id,
                amount=item.price * data.quantity,
                idempotency_key=str(order.id),
            )
        except PaymentCreationFailed:
            order.cancel()
            async with self._uow as uow:
                await uow.orders.update(order)
                await uow.commit()

        return order

    async def _find_by_key(self, key: str) -> Order | None:
        async with self._uow as uow:
            return await uow.orders.get_by_idempotency_key(key)
