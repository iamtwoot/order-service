import logging
from typing import Any

import httpx

from src.application.ports.messaging import MessagePublisher, PublishFailed

logger = logging.getLogger(__name__)


class HttpNotificationsPublisher(MessagePublisher):
    def __init__(self, base_url: str, api_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Api-Key": api_token},
            timeout=5.0,
        )

    async def publish(self, key: str, payload: dict[str, Any]) -> None:
        try:
            response = await self._client.post("/api/notifications", json=payload)
        except httpx.TransportError as e:
            raise PublishFailed(str(e)) from e

        if response.is_client_error:
            logger.error(
                "Notification for %s rejected with %s: %s",
                key,
                response.status_code,
                response.text,
            )
            return
        if response.is_server_error:
            raise PublishFailed(f"Notifications responded with {response.status_code}")
