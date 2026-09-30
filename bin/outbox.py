import asyncio
from contextlib import suppress

from src.container import Container
from src.log_config import configure_logging
from src.presentation.workers.lifecycle import cancel_on_sigterm
from src.presentation.workers.outbox import run_outbox_worker
from src.settings import Settings


async def main() -> None:
    cancel_on_sigterm()
    container = Container(settings=Settings())
    publisher = container.publisher()
    await publisher.start()
    try:
        with suppress(asyncio.CancelledError):
            await asyncio.gather(
                run_outbox_worker(container.publish_order_events()),
                run_outbox_worker(container.publish_notifications()),
            )
    finally:
        await publisher.stop()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
