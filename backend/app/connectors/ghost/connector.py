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
)
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.config import settings

class GhostConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
        if not destination.url and not connection.settings.get("admin_api_url"):
            violations.append("Ghost destination requires admin_api_url in settings or destination url")
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
                message="Ghost Admin API rate limit exceeded (429)",
                details={"retry_after_seconds": 30},
            )
        if simulate_fail == "auth_expired":
            raise IncuBrixException(
                code=ErrorCode.CONNECTION_AUTH_EXPIRED,
                message="Ghost Admin API key invalid or expired (401)",
            )
        if simulate_fail == "content_rejected":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_CONTENT_REJECTED,
                message="Ghost rejected article: Validation failed on post title",
            )

        admin_url = connection.settings.get("admin_api_url") or destination.url.rstrip("/")

        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            h = hashlib.sha256(f"ghost:{idempotency_key}".encode()).hexdigest()[:8]
            post_id = f"ghost_{h}"
            live_url = f"{admin_url}/{h}/"
            return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

        api_key = connection.credentials.get("api_key", "")
        # Real Ghost Admin API call
        headers = {
            "Authorization": f"Ghost {api_key}" if api_key else "",
            "Content-Type": "application/json",
        }
        # Simple markdown to HTML wrap
        html_body = f"<p>{rendition.body.replace(chr(10), '<br/>')}</p>"
        payload = {
            "posts": [
                {
                    "title": rendition.title,
                    "html": html_body,
                    "status": "published",
                    "canonical_url": rendition.canonical_url,
                    "tags": [{"name": t} for t in rendition.tags],
                }
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{admin_url}/ghost/api/admin/posts/?source=html",
                    json=payload,
                    headers=headers,
                )
                if res.status_code != 201:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Ghost error: {res.text}", status_code=res.status_code)
                data = res.json()
                post = data.get("posts", [{}])[0]
                pid = str(post.get("id"))
                live_url = post.get("url") or f"{admin_url}/{pid}/"
                return PublishResponse(platform_post_id=pid, live_url=live_url, status="live")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        admin_url = connection.settings.get("admin_api_url", "https://blog.example.com").rstrip("/")
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return GetStatusResponse(status="live", live_url=f"{admin_url}/p/{platform_post_id}")

        api_key = connection.credentials.get("api_key", "")
        headers = {"Authorization": f"Ghost {api_key}" if api_key else ""}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{admin_url}/ghost/api/admin/posts/{platform_post_id}/", headers=headers)
                if res.status_code == 404:
                    return GetStatusResponse(status="deleted", live_url="")
                if res.status_code != 200:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Ghost get_status failed: {res.text}")
                data = res.json()
                post = data.get("posts", [{}])[0]
                status_str = "live" if post.get("status") == "published" else post.get("status", "draft")
                return GetStatusResponse(status=status_str, live_url=post.get("url", ""))
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return DeleteResponse(deleted=True)

        admin_url = connection.settings.get("admin_api_url", "").rstrip("/")
        api_key = connection.credentials.get("api_key", "")
        headers = {"Authorization": f"Ghost {api_key}" if api_key else ""}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.delete(f"{admin_url}/ghost/api/admin/posts/{platform_post_id}/", headers=headers)
                if res.status_code in (200, 204, 404):
                    return DeleteResponse(deleted=True)
                code = self.map_http_status(res.status_code)
                raise IncuBrixException(code=code, message=f"Ghost delete failed: {res.text}")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))
