from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities import OrderStatus


class CreateOrderRequest(BaseModel):
    user_id: str = Field(min_length=1)
    item_id: UUID
    quantity: int = Field(gt=0)
    idempotency_key: str = Field(min_length=1)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    item_id: str
    quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class PaymentCallbackRequest(BaseModel):
    payment_id: str
    order_id: UUID
    status: Literal["succeeded", "failed"]
    amount: Decimal
    error_message: str | None = None
