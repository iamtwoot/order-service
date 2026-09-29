from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CatalogItem:
    id: str
    price: Decimal
    available_qty: int


class CatalogUnavailable(Exception):
    pass


class CatalogClient(ABC):
    @abstractmethod
    async def get_item(self, item_id: str) -> CatalogItem | None: ...


class PaymentCreationFailed(Exception):
    pass


class PaymentsClient(ABC):
    @abstractmethod
    async def create_payment(
        self, order_id: UUID, amount: Decimal, idempotency_key: str
    ) -> None:
        """Raises PaymentCreationFailed if the payment was not created."""
