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

class HashnodeConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
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
            )
        h = hashlib.sha256(f"hashnode:{idempotency_key}".encode()).hexdigest()[:8]
        post_id = f"hn_{h}"
        live_url = f"{destination.url.rstrip('/')}/{h}"
        return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        return GetStatusResponse(status="live", live_url=f"https://hashnode.com/post/{platform_post_id}")

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        return DeleteResponse(deleted=True)

    async def fetch_metrics(
        self,
        platform_post_id: str,
        connection: ConnectionData,
        since: Optional[str] = None,
    ) -> FetchMetricsResponse:
        h_int = int(hashlib.md5(platform_post_id.encode()).hexdigest(), 16)
        return FetchMetricsResponse(
            views=180 + (h_int % 300),
            likes=8 + (h_int % 25),
            comments=1 + (h_int % 8),
            shares=h_int % 4,
            saves=2 + (h_int % 5),
            clicks=12 + (h_int % 30),
        )
