from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Order


class OrderRepository(ABC):
    @abstractmethod
    async def add(self, order: Order) -> None: ...

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None: ...
