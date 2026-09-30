from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.domain.entities import Order


@dataclass(frozen=True)
class CreateOrderInput:
    user_id: str
    item_id: str
    quantity: int
    idempotency_key: str


class CreateOrderPort(ABC):
    @abstractmethod
    async def __call__(self, data: CreateOrderInput) -> Order: ...


class GetOrderPort(ABC):
    @abstractmethod
    async def __call__(self, order_id: UUID) -> Order: ...


@dataclass(frozen=True)
class PaymentCallbackInput:
    order_id: UUID
    succeeded: bool
    error_message: str | None = None


class HandlePaymentCallbackPort(ABC):
    @abstractmethod
    async def __call__(self, data: PaymentCallbackInput) -> None: ...


class PublishOutboxMessagesPort(ABC):
    @abstractmethod
    async def __call__(self) -> int: ...


@dataclass(frozen=True)
class ShipmentEventInput:
    message_id: str
    order_id: UUID
    shipped: bool
    payload: dict[str, Any]


class HandleShipmentEventPort(ABC):
    @abstractmethod
    async def __call__(self, data: ShipmentEventInput) -> None: ...
