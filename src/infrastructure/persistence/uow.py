from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.ports.uow import UnitOfWork
from src.infrastructure.persistence.repositories import (
    SQLAlchemyInboxRepository,
    SQLAlchemyOrderRepository,
    SQLAlchemyOutboxRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    _session: AsyncSession

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.orders = SQLAlchemyOrderRepository(self._session)
        self.outbox = SQLAlchemyOutboxRepository(self._session)
        self.inbox = SQLAlchemyInboxRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()
