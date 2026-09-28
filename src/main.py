from fastapi import FastAPI

from src.presentation.api.routes import health


def create_app() -> FastAPI:
    app = FastAPI(title="Order Service")
    app.include_router(health.router)
    return app
