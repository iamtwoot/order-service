from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogItem:
    id: str
    available_qty: int


class CatalogUnavailable(Exception):
    pass


class CatalogClient(ABC):
    @abstractmethod
    async def get_item(self, item_id: str) -> CatalogItem | None: ...
