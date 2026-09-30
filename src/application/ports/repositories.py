from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
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


class OutboxDestination(StrEnum):
    ORDER_EVENTS = "order_events"
    NOTIFICATIONS = "notifications"


@dataclass(frozen=True)
class OutboxMessage:
    destination: OutboxDestination
    key: str
    payload: dict[str, Any]
    id: UUID = field(default_factory=uuid4)


class OutboxRepository(ABC):
    @abstractmethod
    async def add(self, message: OutboxMessage) -> None: ...

    @abstractmethod
    async def get_pending(
        self, destination: OutboxDestination, limit: int
    ) -> list[OutboxMessage]:
        """Lock returned rows until commit; rows locked by others are skipped."""

    @abstractmethod
    async def mark_sent(self, message_ids: list[UUID]) -> None: ...


class MessageAlreadyProcessed(Exception):
    pass


class InboxRepository(ABC):
    @abstractmethod
    async def add(self, message_id: str, payload: dict[str, Any]) -> None:
        """Raises MessageAlreadyProcessed if message_id is already in the inbox."""
