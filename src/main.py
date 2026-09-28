from fastapi import FastAPI

from src.presentation.api.dependencies import Container
from src.presentation.api.routes import health
from src.settings import Settings


def create_app() -> FastAPI:
    container = Container(settings=Settings())
    container.wire(modules=[health])

    app = FastAPI(title="Order Service")
    app.include_router(health.router)
    return app
