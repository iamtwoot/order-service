from fastapi import FastAPI

from src.container import Container
from src.presentation.api.routes import health, orders
from src.settings import Settings


def create_app() -> FastAPI:
    container = Container(settings=Settings())
    container.wire(modules=[health, orders])

    app = FastAPI(title="Order Service")
    app.include_router(health.router)
    app.include_router(orders.router)
    return app
