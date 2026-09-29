import logging
from uuid import UUID

from src.application.ports.messaging import MessagePublisher, PublishFailed
from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import PublishOutboxMessagesPort

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class PublishOutboxMessages(PublishOutboxMessagesPort):
    def __init__(self, uow: UnitOfWork, publisher: MessagePublisher) -> None:
        self._uow = uow
        self._publisher = publisher

    async def __call__(self) -> int:
        async with self._uow as uow:
            messages = await uow.outbox.get_pending(limit=BATCH_SIZE)
            sent: list[UUID] = []
            for message in messages:
                try:
                    await self._publisher.publish(message.key, message.payload)
                except PublishFailed:
                    logger.exception("Failed to publish outbox message %s", message.id)
                    break
                sent.append(message.id)

            if sent:
                await uow.outbox.mark_sent(sent)
                await uow.commit()
                logger.info("Published %d outbox messages", len(sent))
            return len(sent)
