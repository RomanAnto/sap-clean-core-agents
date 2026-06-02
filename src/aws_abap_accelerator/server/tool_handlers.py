"""Tool handler stubs — implement against your SAP ADT client."""
from __future__ import annotations
from typing import Optional
import json


class ToolHandlers:
    def __init__(self, sap_client) -> None:
        self._client = sap_client

    async def handle_connection_status(self) -> str:
        result = await self._client.get_connection_status()
        return json.dumps(result)

    async def handle_get_objects(
        self, package_name: Optional[str], object_type: Optional[str]
    ) -> str:
        result = await self._client.get_objects(package_name, object_type)
        return json.dumps(result)

    async def handle_get_source_code(self, object_name: str, object_type: str) -> str:
        result = await self._client.get_source_code(object_name, object_type)
        return json.dumps(result)

    async def handle_run_atc_check(
        self, object_name: str, object_type: str, atc_variant: Optional[str]
    ) -> str:
        result = await self._client.run_atc_check(object_name, object_type, atc_variant)
        return json.dumps(result)

    async def handle_get_where_used(self, object_name: str, object_type: str) -> str:
        result = await self._client.get_where_used(object_name, object_type)
        return json.dumps(result)

    async def handle_search_objects(
        self, query: str, object_type: Optional[str]
    ) -> str:
        result = await self._client.search_objects(query, object_type)
        return json.dumps(result)

    async def handle_activate_objects(self, object_name: str, object_type: str) -> str:
        result = await self._client.activate_objects(object_name, object_type)
        return json.dumps(result)

    async def handle_create_transport(self, description: str, transport_type: str) -> str:
        result = await self._client.create_transport(description, transport_type)
        return json.dumps(result)
