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
    BuildAssistPackResponse,
    AssistPackFile,
)
from backend.app.core.errors import IncuBrixException, ErrorCode

class AssistedConnector(BaseConnector):
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
        """
        Assisted publishing: automation is not permitted by this platform/community.
        We build the assist pack and return status 'manual_action_required'.
        We do NOT pretend an automated API call succeeded.
        """
        val = await self.validate(rendition, destination, connection)
        if not val.ok:
            raise IncuBrixException(
                code=ErrorCode.DEST_SPEC_VIOLATION,
                message=f"Validation failed: {'; '.join(val.violations)}",
                details={"violations": val.violations},
            )

        pack = await self.build_assist_pack(rendition, destination)
        return PublishResponse(
            platform_post_id=f"assist_{idempotency_key[:8]}",
            live_url=destination.url,
            status="manual_action_required",
        )

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        return GetStatusResponse(
            status="manual_action_required",
            live_url="",
        )

    async def delete(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> DeleteResponse:
        return DeleteResponse(deleted=True)

    async def build_assist_pack(
        self,
        rendition: RenditionData,
        destination: DestinationData,
    ) -> BuildAssistPackResponse:
        caption = f"{rendition.title}\n\n{rendition.body}"
        if rendition.contains_ai_content and rendition.ai_disclosure_statement:
            caption += f"\n\n---\n{rendition.ai_disclosure_statement}"

        checklist = [
            f"Review destination rules at: {destination.rules_url or destination.url}",
            f"Verify frequency cap not exceeded (Frequency: {destination.frequency_cap})",
        ]
        if destination.self_promo_allowed:
            checklist.append("Self-promotion allowed: ensure content adds genuine value to community discussion.")
        else:
            checklist.append("Strict no-promotion rule: ensure post contains zero promotional or commercial links.")

        if destination.disclosure_required:
            checklist.append("Mandatory AI Disclosure: ensure AI generation notice is included in your post.")

        files: List[AssistPackFile] = []
        for i, url in enumerate(rendition.media_urls):
            files.append(
                AssistPackFile(
                    name=f"media_{i+1}",
                    url=url,
                    type="media",
                )
            )

        return BuildAssistPackResponse(
            files=files,
            caption=caption,
            deep_link=destination.url,
            checklist=checklist,
        )
