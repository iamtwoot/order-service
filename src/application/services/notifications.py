from src.application.ports.repositories import OutboxDestination, OutboxMessage
from src.domain.entities import Order, OrderStatus

MESSAGES = {
    OrderStatus.NEW: "Ваш заказ создан и ожидает оплаты",
    OrderStatus.PAID: "Ваш заказ успешно оплачен и готов к отправке",
    OrderStatus.SHIPPED: "Ваш заказ отправлен в доставку",
    OrderStatus.CANCELLED: "Ваш заказ отменен. Причина: {reason}",
}


def status_notification(order: Order, reason: str | None = None) -> OutboxMessage:
    text = MESSAGES[order.status].format(reason=reason or "не указана")
    return OutboxMessage(
        destination=OutboxDestination.NOTIFICATIONS,
        key=str(order.id),
        payload={
            "message": f"[{order.status}] {text}",
            "reference_id": str(order.id),
            "idempotency_key": f"{order.id}:{order.status}",
        },
    )
