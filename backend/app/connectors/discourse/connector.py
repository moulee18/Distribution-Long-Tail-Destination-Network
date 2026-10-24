import hashlib
import time
from typing import Any, Dict, List, Optional
import httpx

from backend.app.connectors.base.connector import BaseConnector
from backend.app.connectors.base.manifest import ConnectorManifest
from backend.app.schemas.connector_contract import (
    RenditionData,
    DestinationData,
    ConnectionData,
    ValidateResponse,
    PublishResponse,
    GetStatusResponse,
    DeleteResponse,
    FetchMetricsResponse,
)
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.config import settings

class DiscourseConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
        if not destination.url and not connection.settings.get("base_url"):
            violations.append("Discourse destination requires base_url in url or connection settings")
        return ValidateResponse(ok=len(violations) == 0, violations=violations)

    async def publish(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
        idempotency_key: str,
    ) -> PublishResponse:
        val = await self.validate(rendition, destination, connection)
        if not val.ok:
            raise IncuBrixException(
                code=ErrorCode.DEST_SPEC_VIOLATION,
                message=f"Validation failed: {'; '.join(val.violations)}",
                details={"violations": val.violations},
            )

        # Check simulation mode or failure injections
        simulate_fail = connection.settings.get("simulate_failure")
        if simulate_fail == "rate_limit":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_RATE_LIMIT,
                message="Discourse rate limit reached (429)",
                details={"retry_after_seconds": 30},
            )
        if simulate_fail == "auth_expired":
            raise IncuBrixException(
                code=ErrorCode.CONNECTION_AUTH_EXPIRED,
                message="Discourse API Key expired or invalid (401)",
            )
        if simulate_fail == "content_rejected":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_CONTENT_REJECTED,
                message="Discourse rejected content: Body contains forbidden spam phrase",
            )
        if simulate_fail == "timeout":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_UNAVAILABLE,
                message="Connection timed out while publishing to Discourse",
            )

        base_url = connection.settings.get("base_url") or destination.url.rstrip("/")
        api_key = connection.credentials.get("api_key")
        api_username = connection.credentials.get("api_username", "system")

        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            # Deterministic platform post id based on idempotency_key
            h = hashlib.sha256(f"discourse:{idempotency_key}".encode()).hexdigest()[:10]
            post_id = f"disc_{h}"
            live_url = f"{base_url}/t/topic-{h}/{post_id}"
            return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

        # Real HTTP call to Discourse
        headers = {
            "Api-Key": api_key or "",
            "Api-Username": api_username,
            "Content-Type": "application/json",
        }
        payload = {
            "title": rendition.title,
            "raw": rendition.body,
            "category": connection.settings.get("category_id"),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{base_url}/posts.json", json=payload, headers=headers)
                if res.status_code != 200 and res.status_code != 201:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(
                        code=code,
                        message=f"Discourse error: {res.text}",
                        status_code=res.status_code,
                    )
                data = res.json()
                post_id = str(data.get("id"))
                topic_id = data.get("topic_id")
                topic_slug = data.get("topic_slug", "topic")
                live_url = f"{base_url}/t/{topic_slug}/{topic_id}/{post_id}"
                return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")
        except httpx.RequestError as e:
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_UNAVAILABLE,
                message=f"Discourse request error: {str(e)}",
            )

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        simulate_fail = connection.settings.get("simulate_failure")
        if simulate_fail == "schema_change":
            # Simulate a changed API schema causing failure
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_CONTENT_REJECTED,
                message="Discourse API response schema unexpected: missing post fields",
            )

        base_url = connection.settings.get("base_url", "https://forum.example.com").rstrip("/")
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return GetStatusResponse(
                status="live",
                live_url=f"{base_url}/posts/{platform_post_id}",
            )

        api_key = connection.credentials.get("api_key")
        api_username = connection.credentials.get("api_username", "system")
        headers = {"Api-Key": api_key or "", "Api-Username": api_username}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{base_url}/posts/{platform_post_id}.json", headers=headers)
                if res.status_code == 404:
                    return GetStatusResponse(status="deleted", live_url="")
                if res.status_code != 200:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Discourse get_status failed: {res.text}")
                data = res.json()
                topic_id = data.get("topic_id")
                return GetStatusResponse(
                    status="live",
                    live_url=f"{base_url}/t/{topic_id}/{platform_post_id}",
                )
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return DeleteResponse(deleted=True)

        base_url = connection.settings.get("base_url", "").rstrip("/")
        api_key = connection.credentials.get("api_key")
        api_username = connection.credentials.get("api_username", "system")
        headers = {"Api-Key": api_key or "", "Api-Username": api_username}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.delete(f"{base_url}/posts/{platform_post_id}.json", headers=headers)
                if res.status_code in (200, 204, 404):
                    return DeleteResponse(deleted=True)
                code = self.map_http_status(res.status_code)
                raise IncuBrixException(code=code, message=f"Discourse delete failed: {res.text}")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def fetch_metrics(
        self,
        platform_post_id: str,
        connection: ConnectionData,
        since: Optional[str] = None,
    ) -> FetchMetricsResponse:
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            h_int = int(hashlib.md5(platform_post_id.encode()).hexdigest(), 16)
            return FetchMetricsResponse(
                views=100 + (h_int % 400),
                likes=5 + (h_int % 30),
                comments=2 + (h_int % 15),
                shares=1 + (h_int % 5),
                saves=h_int % 8,
                clicks=10 + (h_int % 50),
            )
        return FetchMetricsResponse(views=0, likes=0, comments=0, shares=0, saves=0, clicks=0)
