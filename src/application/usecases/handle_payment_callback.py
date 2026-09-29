import logging

from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import (
    HandlePaymentCallbackPort,
    PaymentCallbackInput,
)
from src.domain.exceptions import OrderNotFound

logger = logging.getLogger(__name__)


class HandlePaymentCallback(HandlePaymentCallbackPort):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self, data: PaymentCallbackInput) -> None:
        async with self._uow as uow:
            order = await uow.orders.get_by_id(data.order_id, for_update=True)
            if order is None:
                raise OrderNotFound(data.order_id)

            changed = (
                order.mark_paid() if data.succeeded else order.mark_payment_failed()
            )
            if not changed:
                logger.info("Repeated callback for order %s ignores", order.id)

            await uow.orders.update(order)
            await uow.commit()
        logger.info("Order %s is now %s", order.id, order.status)
