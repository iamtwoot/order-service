from decimal import Decimal
from uuid import UUID

import httpx

from src.application.ports.clients import PaymentCreationFailed, PaymentsClient


class HttpPaymentsClient(PaymentsClient):
    def __init__(self, base_url: str, api_token: str, callback_url: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Api-Key": api_token},
            timeout=5.0,
        )
        self._callback_url = callback_url

    async def create_payment(
        self, order_id: UUID, amount: Decimal, idempotency_key: str
    ) -> None:
        try:
            response = await self._client.post(
                "/api/payments",
                json={
                    "order_id": str(order_id),
                    "amount": str(amount),
                    "callback_url": self._callback_url,
                    "idempotency_key": idempotency_key,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise PaymentCreationFailed(str(e)) from e
