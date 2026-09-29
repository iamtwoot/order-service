from abc import ABC, abstractmethod
from typing import Any


class PublishFailed(Exception):
    pass


class MessagePublisher(ABC):
    @abstractmethod
    async def publish(self, key: str, payload: dict[str, Any]) -> None:
        """Raises PublishFailed if the broker did not confirm the message."""
