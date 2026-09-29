from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from src.domain.exceptions import InvalidStatusTransition


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.NEW: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: set(),
    OrderStatus.CANCELLED: set(),
}


@dataclass
class Order:
    id: UUID
    user_id: str
    item_id: str
    quantity: int
    idempotency_key: str
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        item_id: str,
        quantity: int,
        idempotency_key: str,
    ) -> "Order":
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            status=OrderStatus.NEW,
            created_at=now,
            updated_at=now,
        )

    def mark_paid(self) -> bool:
        return self._transition_to(OrderStatus.PAID)

    def mark_payment_failed(self) -> bool:
        if self.status == OrderStatus.PAID:
            raise InvalidStatusTransition("Paid order cannot fail payment")
        return self.cancel()

    def cancel(self) -> bool:
        return self._transition_to(OrderStatus.CANCELLED)

    def _transition_to(self, new_status: OrderStatus) -> bool:
        if self.status == new_status:
            return False
        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransition(f"{self.status} -> {new_status}")
        self.status = new_status
        self.updated_at = datetime.now(UTC)
        return True
