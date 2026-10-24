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

class LemmyConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
        if not destination.url and not connection.settings.get("instance_url"):
            violations.append("Lemmy destination requires instance_url in destination or settings")
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
                message="Lemmy instance rate limit exceeded (429)",
                details={"retry_after_seconds": 60},
            )
        if simulate_fail == "auth_expired":
            raise IncuBrixException(
                code=ErrorCode.CONNECTION_AUTH_EXPIRED,
                message="Lemmy JWT token expired or invalid (401)",
            )
        if simulate_fail == "content_rejected":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_CONTENT_REJECTED,
                message="Lemmy community rejected post: duplicate title in community",
            )

        instance_url = connection.settings.get("instance_url") or destination.url.rstrip("/")
        community_id = connection.settings.get("community_id", 1)

        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            h = hashlib.sha256(f"lemmy:{idempotency_key}".encode()).hexdigest()[:8]
            post_id = f"lemmy_{h}"
            live_url = f"{instance_url}/post/{post_id}"
            return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

        auth_token = connection.credentials.get("auth_token")
        headers = {"Authorization": f"Bearer {auth_token}" if auth_token else ""}
        payload = {
            "name": rendition.title,
            "body": rendition.body,
            "community_id": int(community_id),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{instance_url}/api/v3/post", json=payload, headers=headers)
                if res.status_code != 200:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Lemmy error: {res.text}", status_code=res.status_code)
                data = res.json()
                post_view = data.get("post_view", {})
                post = post_view.get("post", {})
                pid = str(post.get("id"))
                live_url = f"{instance_url}/post/{pid}"
                return PublishResponse(platform_post_id=pid, live_url=live_url, status="live")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        instance_url = connection.settings.get("instance_url", "https://lemmy.world").rstrip("/")
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return GetStatusResponse(status="live", live_url=f"{instance_url}/post/{platform_post_id}")

        auth_token = connection.credentials.get("auth_token")
        headers = {"Authorization": f"Bearer {auth_token}" if auth_token else ""}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{instance_url}/api/v3/post?id={platform_post_id}", headers=headers)
                if res.status_code == 404:
                    return GetStatusResponse(status="deleted", live_url="")
                if res.status_code != 200:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Lemmy get_status failed: {res.text}")
                data = res.json()
                deleted = data.get("post_view", {}).get("post", {}).get("deleted", False)
                if deleted:
                    return GetStatusResponse(status="deleted", live_url="")
                return GetStatusResponse(status="live", live_url=f"{instance_url}/post/{platform_post_id}")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return DeleteResponse(deleted=True)

        instance_url = connection.settings.get("instance_url", "").rstrip("/")
        auth_token = connection.credentials.get("auth_token")
        headers = {"Authorization": f"Bearer {auth_token}" if auth_token else ""}
        payload = {"post_id": int(platform_post_id) if platform_post_id.isdigit() else platform_post_id, "deleted": True}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{instance_url}/api/v3/post/delete", json=payload, headers=headers)
                if res.status_code in (200, 204):
                    return DeleteResponse(deleted=True)
                code = self.map_http_status(res.status_code)
                raise IncuBrixException(code=code, message=f"Lemmy delete failed: {res.text}")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))
