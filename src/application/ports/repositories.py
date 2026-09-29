from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Order


class OrderAlreadyExists(Exception):
    pass


class OrderRepository(ABC):
    @abstractmethod
    async def add(self, order: Order) -> None:
        """Raise OrderAlreadyExists if idempotency_key is already taken."""

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None: ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Order | None: ...

    @abstractmethod
    async def update(self, order: Order) -> None: ...
