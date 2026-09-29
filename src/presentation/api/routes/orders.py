from uuid import UUID

from dependency_injector.wiring import inject
from fastapi import APIRouter, HTTPException, status

from src.application.ports.clients import CatalogUnavailable
from src.application.ports.usecases import CreateOrderInput
from src.domain.exceptions import InsufficientStock, ItemNotFound, OrderNotFound
from src.presentation.api.dependencies import CreateOrderDep, GetOrderDep
from src.presentation.api.schemas import CreateOrderRequest, OrderResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_order(
    body: CreateOrderRequest,
    create_order: CreateOrderDep,
) -> OrderResponse:
    try:
        order = await create_order(
            CreateOrderInput(
                user_id=body.user_id,
                item_id=str(body.item_id),
                quantity=body.quantity,
                idempotency_key=body.idempotency_key,
            )
        )
    except ItemNotFound:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Item not found") from None
    except InsufficientStock:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Insufficient stock") from None
    except CatalogUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Catalog service unavailable"
        ) from None
    return OrderResponse.model_validate(order)


@router.get("/{order_id}")
@inject
async def get_order(order_id: UUID, get_order: GetOrderDep) -> OrderResponse:
    try:
        order = await get_order(order_id)
    except OrderNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found") from None
    return OrderResponse.model_validate(order)
