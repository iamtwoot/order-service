from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


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

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now(UTC)
