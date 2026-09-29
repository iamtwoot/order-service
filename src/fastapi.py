import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from src.presentation.api.dependencies import Container
from src.presentation.api.routes import health, orders
from src.presentation.workers.outbox import run_outbox_worker
from src.settings import Settings


def create_app() -> FastAPI:
    container = Container(settings=Settings())
    container.wire(modules=[health, orders])

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        publisher = container.publisher()
        await publisher.start()
        outbox_worker = asyncio.create_task(
            run_outbox_worker(container.publish_outbox_messages())
        )
        yield
        outbox_worker.cancel()
        with suppress(asyncio.CancelledError):
            await outbox_worker
        await publisher.stop()

    app = FastAPI(title="Order Service", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(orders.router)
    return app
