from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from src.domain.entities import Order


class OrderAlreadyExists(Exception):
    pass


class OrderRepository(ABC):
    @abstractmethod
    async def add(self, order: Order) -> None:
        """Raise OrderAlreadyExists if idempotency_key is already taken."""

    @abstractmethod
    async def get_by_id(
        self, order_id: UUID, *, for_update: bool = False
    ) -> Order | None: ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Order | None: ...

    @abstractmethod
    async def update(self, order: Order) -> None: ...


@dataclass(frozen=True)
class OutboxMessage:
    key: str
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)


class OutboxRepository(ABC):
    @abstractmethod
    async def add(self, message: OutboxMessage) -> None: ...
