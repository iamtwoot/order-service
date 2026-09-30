from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.container import Container

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
@inject
async def health_db(
    engine: Annotated[AsyncEngine, Depends(Provide[Container.engine])],
) -> dict[str, str]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
