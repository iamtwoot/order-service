import asyncio
import logging

from src.application.ports.usecases import PublishOutboxMessagesPort

logger = logging.getLogger(__name__)


async def run_outbox_worker(
    publish: PublishOutboxMessagesPort, interval: float = 1.0
) -> None:
    while True:
        try:
            sent = await publish()
        except Exception:
            logger.exception("Outbox worker iteration failed")
            sent = 0
        if sent == 0:
            await asyncio.sleep(interval)
