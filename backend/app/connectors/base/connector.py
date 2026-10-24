from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
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
    RefreshAuthResponse,
    BuildAssistPackResponse,
)
from backend.app.core.errors import IncuBrixException, ErrorCode

class BaseConnector(ABC):
    def __init__(self, manifest: ConnectorManifest):
        self.manifest = manifest
        self.key = manifest.key
        self.enabled = True

    def validate_spec(self, rendition: RenditionData, surface_key: Optional[str] = None) -> List[str]:
        violations: List[str] = []
        surface = self.manifest.surfaces[0]
        if surface_key:
            for s in self.manifest.surfaces:
                if s.key == surface_key:
                    surface = s
                    break
        
        spec = surface.spec
        if len(rendition.title) > spec.title_max_chars:
            violations.append(f"Title exceeds maximum length of {spec.title_max_chars} chars (got {len(rendition.title)})")
        if len(rendition.body) > spec.body_max_chars:
            violations.append(f"Body exceeds maximum length of {spec.body_max_chars} chars (got {len(rendition.body)})")
        if not spec.links_allowed and ("[http" in rendition.body or "http://" in rendition.body or "https://" in rendition.body):
            violations.append("Links are not allowed on this surface")
        if spec.max_tags and len(rendition.tags) > spec.max_tags:
            violations.append(f"Tags count exceeds maximum of {spec.max_tags} (got {len(rendition.tags)})")
        
        return violations

    @abstractmethod
    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        pass

    @abstractmethod
    async def publish(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
        idempotency_key: str,
    ) -> PublishResponse:
        pass

    @abstractmethod
    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        pass

    @abstractmethod
    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        pass

    async def fetch_metrics(
        self,
        platform_post_id: str,
        connection: ConnectionData,
        since: Optional[str] = None,
    ) -> FetchMetricsResponse:
        raise IncuBrixException(
            code=ErrorCode.DEST_SPEC_VIOLATION,
            message=f"Connector {self.key} does not support metrics",
            status_code=400,
        )

    async def refresh_auth(
        self,
        connection: ConnectionData,
    ) -> RefreshAuthResponse:
        raise IncuBrixException(
            code=ErrorCode.DEST_SPEC_VIOLATION,
            message=f"Connector {self.key} does not support auth refresh",
            status_code=400,
        )

    async def build_assist_pack(
        self,
        rendition: RenditionData,
        destination: DestinationData,
    ) -> BuildAssistPackResponse:
        raise IncuBrixException(
            code=ErrorCode.DEST_SPEC_VIOLATION,
            message=f"Connector {self.key} does not support build_assist_pack",
            status_code=400,
        )

    def map_http_status(self, http_status: int, response_body: Optional[str] = None) -> ErrorCode:
        status_str = str(http_status)
        if status_str in self.manifest.error_map:
            mapped = self.manifest.error_map[status_str]
            return ErrorCode(mapped)
        if http_status == 401 or http_status == 403:
            return ErrorCode.CONNECTION_AUTH_EXPIRED
        if http_status == 429:
            return ErrorCode.PLATFORM_RATE_LIMIT
        if http_status == 422 or http_status == 400:
            return ErrorCode.PLATFORM_CONTENT_REJECTED
        if http_status >= 500:
            return ErrorCode.PLATFORM_UNAVAILABLE
        return ErrorCode.PLATFORM_UNAVAILABLE
