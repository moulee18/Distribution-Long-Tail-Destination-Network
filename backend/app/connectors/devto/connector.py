import hashlib
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

class DevtoConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
        if len(rendition.tags) > 4:
            violations.append("Dev.to allows a maximum of 4 tags")
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

        simulate_fail = connection.settings.get("simulate_failure")
        if simulate_fail == "rate_limit":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_RATE_LIMIT,
                message="Dev.to API rate limit reached (429)",
                details={"retry_after_seconds": 30},
            )
        if simulate_fail == "auth_expired":
            raise IncuBrixException(
                code=ErrorCode.CONNECTION_AUTH_EXPIRED,
                message="Dev.to api-key invalid or expired (401)",
            )
        if simulate_fail == "content_rejected":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_CONTENT_REJECTED,
                message="Dev.to rejected article: spam filter triggered (422)",
            )

        base_url = connection.settings.get("api_base_url", "https://dev.to/api").rstrip("/")
        api_key = connection.credentials.get("api_key")

        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            h = hashlib.sha256(f"devto:{idempotency_key}".encode()).hexdigest()[:8]
            post_id = f"devto_{h}"
            live_url = f"https://dev.to/incubrix/article-{h}"
            return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

        headers = {"api-key": api_key or "", "Content-Type": "application/json"}
        tags = [t.replace("#", "").replace(" ", "").lower() for t in rendition.tags][:4]
        payload = {
            "article": {
                "title": rendition.title,
                "body_markdown": rendition.body,
                "published": True,
                "tags": tags,
                "canonical_url": rendition.canonical_url,
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{base_url}/articles", json=payload, headers=headers)
                if res.status_code != 201:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Dev.to error: {res.text}", status_code=res.status_code)
                data = res.json()
                pid = str(data.get("id"))
                live_url = data.get("url") or f"https://dev.to/articles/{pid}"
                return PublishResponse(platform_post_id=pid, live_url=live_url, status="live")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        base_url = connection.settings.get("api_base_url", "https://dev.to/api").rstrip("/")
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return GetStatusResponse(status="live", live_url=f"https://dev.to/articles/{platform_post_id}")

        api_key = connection.credentials.get("api_key")
        headers = {"api-key": api_key or ""}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{base_url}/articles/{platform_post_id}", headers=headers)
                if res.status_code == 404:
                    return GetStatusResponse(status="deleted", live_url="")
                if res.status_code != 200:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Dev.to get_status failed: {res.text}")
                data = res.json()
                published = data.get("published", True)
                status_str = "live" if published else "unpublished"
                return GetStatusResponse(status=status_str, live_url=data.get("url", ""))
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        """
        Dev.to API limitation adapter:
        The public Dev.to API does not provide a hard DELETE endpoint for public articles.
        Our adapter unpublishes the article via PUT /api/articles/{id} with published: false,
        or marks deleted in simulation.
        """
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return DeleteResponse(deleted=True)

        base_url = connection.settings.get("api_base_url", "https://dev.to/api").rstrip("/")
        api_key = connection.credentials.get("api_key")
        headers = {"api-key": api_key or "", "Content-Type": "application/json"}
        payload = {"article": {"published": False}}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.put(f"{base_url}/articles/{platform_post_id}", json=payload, headers=headers)
                if res.status_code in (200, 204, 404):
                    return DeleteResponse(deleted=True)
                code = self.map_http_status(res.status_code)
                raise IncuBrixException(code=code, message=f"Dev.to unpublish failed: {res.text}")
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
                views=250 + (h_int % 500),
                likes=12 + (h_int % 40),
                comments=3 + (h_int % 12),
                shares=h_int % 6,
                saves=4 + (h_int % 10),
                clicks=15 + (h_int % 60),
            )
        base_url = connection.settings.get("api_base_url", "https://dev.to/api").rstrip("/")
        api_key = connection.credentials.get("api_key")
        headers = {"api-key": api_key or ""}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{base_url}/articles/{platform_post_id}", headers=headers)
                if res.status_code == 200:
                    d = res.json()
                    return FetchMetricsResponse(
                        views=d.get("page_views_count", 0),
                        likes=d.get("positive_reactions_count", 0),
                        comments=d.get("comments_count", 0),
                        shares=0,
                        saves=0,
                        clicks=0,
                    )
        except Exception:
            pass
        return FetchMetricsResponse(views=0, likes=0, comments=0, shares=0, saves=0, clicks=0)
