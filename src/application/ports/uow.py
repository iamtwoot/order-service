from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.application.ports.repositories import OrderRepository


class UnitOfWork(ABC):
    orders: OrderRepository

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...
