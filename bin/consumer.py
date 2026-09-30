import asyncio
from contextlib import suppress

from src.container import Container
from src.log_config import configure_logging
from src.presentation.workers.lifecycle import cancel_on_sigterm
from src.settings import Settings


async def main() -> None:
    cancel_on_sigterm()
    container = Container(settings=Settings())
    with suppress(asyncio.CancelledError):
        await container.shipment_event_consumer().run()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
