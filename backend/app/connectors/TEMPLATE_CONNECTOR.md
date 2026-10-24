# Reusable Connector Template Guide

To add a new platform connector (e.g., `peertube` or `mrss`) in under 3 minutes during development or the Live Session:

## Step 1: Create the YAML Manifest (`manifests/<key>.yaml`)
```yaml
key: peertube
version: 1.0.0
tier: protocol
auth: oauth2
surfaces:
  - key: video
    content_types: [video_link, text]
    spec:
      title_max_chars: 120
      body_max_chars: 10000
      links_allowed: true
rate_limits:
  per_connection:
    requests: 30
    per_seconds: 60
capabilities: [publish, status, delete, metrics]
error_map:
  "429": PLATFORM_RATE_LIMIT
  "401": CONNECTION_AUTH_EXPIRED
  "422": PLATFORM_CONTENT_REJECTED
instance_param: instance_url
```

## Step 2: Implement the Connector Class (`backend/app/connectors/<key>/connector.py`)
```python
import hashlib
from typing import Optional
from backend.app.connectors.base.connector import BaseConnector
from backend.app.connectors.base.manifest import ConnectorManifest
from backend.app.schemas.connector_contract import (
    RenditionData, DestinationData, ConnectionData,
    ValidateResponse, PublishResponse, GetStatusResponse, DeleteResponse
)
from backend.app.core.errors import IncuBrixException, ErrorCode

class PeerTubeConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(self, rendition: RenditionData, destination: DestinationData, connection: ConnectionData) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
        return ValidateResponse(ok=len(violations) == 0, violations=violations)

    async def publish(self, rendition: RenditionData, destination: DestinationData, connection: ConnectionData, idempotency_key: str) -> PublishResponse:
        val = await self.validate(rendition, destination, connection)
        if not val.ok:
            raise IncuBrixException(ErrorCode.DEST_SPEC_VIOLATION, "; ".join(val.violations))
        h = hashlib.sha256(f"{self.key}:{idempotency_key}".encode()).hexdigest()[:8]
        return PublishResponse(platform_post_id=f"pt_{h}", live_url=f"{destination.url.rstrip('/')}/w/{h}", status="live")

    async def get_status(self, platform_post_id: str, connection: ConnectionData) -> GetStatusResponse:
        return GetStatusResponse(status="live", live_url=f"https://peertube.example.com/w/{platform_post_id}")

    async def delete(self, platform_post_id: str, connection: ConnectionData) -> DeleteResponse:
        return DeleteResponse(deleted=True)
```

## Step 3: Register in `CONNECTOR_CLASSES` (`backend/app/connectors/registry.py`)
Add `"peertube": PeerTubeConnector` to `CONNECTOR_CLASSES`. All `/connector/v1/peertube/*` endpoints and certification flows are immediately active!
