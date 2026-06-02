"""SAP ADT HTTP client."""
from __future__ import annotations
from typing import Optional
import httpx


class SAPClient:
    """Thin async HTTP client for SAP ADT REST API."""

    def __init__(
        self,
        host: str,
        client: str,
        username: str,
        password: str,
        instance: str = "00",
        secure: bool = True,
        ssl_verify: bool = True,
    ) -> None:
        scheme = "https" if secure else "http"
        port = 443 if secure else 8000
        self._base_url = f"{scheme}://{host}:{port}/sap/bc/adt"
        self._client_num = client
        self._auth = (username, password)
        self._ssl_verify = ssl_verify
        self._http: Optional[httpx.AsyncClient] = None

    def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                auth=self._auth,
                verify=self._ssl_verify,
                headers={
                    "sap-client": self._client_num,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._http

    async def get_connection_status(self) -> dict:
        r = await self._get_http().get(f"{self._base_url}/discovery")
        r.raise_for_status()
        return {"status": "connected", "statusCode": r.status_code}

    async def get_objects(self, package: Optional[str], object_type: Optional[str]) -> dict:
        params = {}
        if package:
            params["packageName"] = package
        if object_type:
            params["objectType"] = object_type
        r = await self._get_http().get(f"{self._base_url}/repository/informationsystem/search", params=params)
        r.raise_for_status()
        return r.json()

    async def get_source_code(self, object_name: str, object_type: str) -> dict:
        r = await self._get_http().get(
            f"{self._base_url}/programs/programs/{object_name}/source/main"
        )
        r.raise_for_status()
        return {"objectName": object_name, "source": r.text}

    async def run_atc_check(
        self, object_name: str, object_type: str, variant: Optional[str]
    ) -> dict:
        payload = {
            "objectName": object_name,
            "objectType": object_type,
            "checkVariant": variant or "ABAP_CLOUD_READINESS_CHECK",
        }
        r = await self._get_http().post(f"{self._base_url}/atc/runs", json=payload)
        r.raise_for_status()
        return r.json()

    async def get_where_used(self, object_name: str, object_type: str) -> dict:
        r = await self._get_http().get(
            f"{self._base_url}/repository/informationsystem/whereused",
            params={"objectName": object_name, "objectType": object_type},
        )
        r.raise_for_status()
        return r.json()

    async def search_objects(self, query: str, object_type: Optional[str]) -> dict:
        params = {"query": query}
        if object_type:
            params["objectType"] = object_type
        r = await self._get_http().get(
            f"{self._base_url}/repository/informationsystem/search", params=params
        )
        r.raise_for_status()
        return r.json()

    async def activate_objects(self, object_name: str, object_type: str) -> dict:
        payload = {"objectName": object_name, "objectType": object_type}
        r = await self._get_http().post(f"{self._base_url}/activation", json=payload)
        r.raise_for_status()
        return {"activated": True, "objectName": object_name}

    async def create_transport(self, description: str, transport_type: str) -> dict:
        payload = {"description": description, "type": transport_type}
        r = await self._get_http().post(f"{self._base_url}/cts/transports", json=payload)
        r.raise_for_status()
        return r.json()

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()
