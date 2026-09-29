import httpx

from src.application.ports.clients import CatalogClient, CatalogItem, CatalogUnavailable


class HttpCatalogClient(CatalogClient):
    def __init__(self, base_url: str, api_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_token},
            timeout=5.0,
        )

    async def get_item(self, item_id: str) -> CatalogItem | None:
        try:
            response = await self._client.get(f"/api/catalog/items/{item_id}")
        except httpx.TransportError as e:
            raise CatalogUnavailable(str(e)) from e

        if response.status_code == httpx.codes.NOT_FOUND:
            return None
        if response.is_server_error:
            raise CatalogUnavailable(f"Catalog responded with {response.status_code}")
        response.raise_for_status()

        data = response.json()
        return CatalogItem(id=data["id"], available_qty=data["available_qty"])
