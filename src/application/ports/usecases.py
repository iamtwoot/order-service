from abc import ABC, abstractmethod
from dataclasses import dataclass
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


class HandlePaymentCallbackPort(ABC):
    @abstractmethod
    async def __call__(self, data: PaymentCallbackInput) -> None: ...
