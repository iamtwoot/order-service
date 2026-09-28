from uuid import UUID

from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, status

from src.application.ports.usecases import CreateOrderInput
from src.domain.exceptions import OrderNotFound
from src.presentation.api.dependencies import CreateOrderDep, GetOrderDep
from src.presentation.api.schemas import CreateOrderRequest, OrderResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_order(
    body: CreateOrderRequest,
    create_order: CreateOrderDep,
) -> OrderResponse:
    order = await create_order(
        CreateOrderInput(
            user_id=body.user_id,
            item_id=body.item_id,
            quantity=body.quantity,
            idempotency_key=body.idempotency_key,
        )
    )
    return OrderResponse.model_validate(order)


@router.get("/{order_id}")
@inject
async def get_order(order_id: UUID, get_order: GetOrderDep) -> OrderResponse:
    try:
        order = await get_order(order_id)
    except OrderNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found") from None
    return OrderResponse.model_validate(order)
