from datetime import datetime
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
