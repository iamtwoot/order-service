import logging

from src.application.ports.repositories import MessageAlreadyProcessed
from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import HandleShipmentEventPort, ShipmentEventInput
from src.application.services.notifications import status_notification
from src.domain.exceptions import InvalidStatusTransition

logger = logging.getLogger(__name__)


class HandleShipmentEvent(HandleShipmentEventPort):
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self, data: ShipmentEventInput) -> None:
        async with self._uow as uow:
            order = await uow.orders.get_by_id(data.order_id, for_update=True)
            if order is None:
                return

            try:
                await uow.inbox.add(data.message_id, data.payload)
            except MessageAlreadyProcessed:
                logger.info("Message %s already processed", data.message_id)
                return

            try:
                changed = order.mark_shipped() if data.shipped else order.cancel()
            except InvalidStatusTransition as e:
                logger.warning("Shipment event for order %s ignored: %s", order.id, e)
                changed = False

            if changed:
                await uow.orders.update(order)
                await uow.outbox.add(
                    status_notification(order, data.payload.get("reason")),
                )
            await uow.commit()

        if changed:
            logger.info("Order %s is now %s", order.id, order.status)
