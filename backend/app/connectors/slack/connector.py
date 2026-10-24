import hashlib
from typing import Any, Dict, List, Optional
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

class SlackConnector(BaseConnector):
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
        h = hashlib.sha256(f"slack:{idempotency_key}".encode()).hexdigest()[:8]
        post_id = f"msg_{h}"
        channel = connection.settings.get("channel_id", "general")
        live_url = f"https://slack.com/app_redirect?channel={channel}&message_ts={h}"
        return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        return GetStatusResponse(status="live", live_url=f"https://slack.com/messages/{platform_post_id}")

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        return DeleteResponse(deleted=True)
