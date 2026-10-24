import hashlib
import hmac
import json
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

def compute_hmac_signature(payload_bytes: bytes, secret: str, timestamp: str) -> str:
    message = timestamp.encode("utf-8") + b"." + payload_bytes
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

class WebhookConnector(BaseConnector):
    def __init__(self, manifest: ConnectorManifest):
        super().__init__(manifest)

    async def validate(
        self,
        rendition: RenditionData,
        destination: DestinationData,
        connection: ConnectionData,
    ) -> ValidateResponse:
        violations = self.validate_spec(rendition, destination.surface)
        webhook_url = connection.settings.get("webhook_url") or destination.url
        if not webhook_url:
            violations.append("Webhook destination requires webhook_url")
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

        # Check partner permission status or failure injection
        if connection.settings.get("permission_revoked") or connection.settings.get("simulate_failure") == "partner_revoked":
            raise IncuBrixException(
                code=ErrorCode.CONNECTION_AUTH_EXPIRED,
                message="Webhook partner has revoked publishing permission",
                status_code=403,
            )

        simulate_fail = connection.settings.get("simulate_failure")
        if simulate_fail == "rate_limit":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_RATE_LIMIT,
                message="Webhook partner rate limit exceeded (429)",
                details={"retry_after_seconds": 60},
            )
        if simulate_fail == "content_rejected":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_CONTENT_REJECTED,
                message="Webhook partner rejected content payload (422)",
            )
        if simulate_fail == "timeout":
            raise IncuBrixException(
                code=ErrorCode.PLATFORM_UNAVAILABLE,
                message="Webhook partner timed out (504)",
            )

        webhook_url = connection.settings.get("webhook_url") or destination.url
        secret = connection.credentials.get("signing_secret") or settings.WEBHOOK_SIGNING_SECRET

        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            h = hashlib.sha256(f"webhook:{idempotency_key}".encode()).hexdigest()[:10]
            post_id = f"wh_{h}"
            live_url = f"{webhook_url}/posts/{post_id}"
            return PublishResponse(platform_post_id=post_id, live_url=live_url, status="live")

        timestamp = str(int(time.time()))
        payload = {
            "event": "publication.created",
            "idempotency_key": idempotency_key,
            "title": rendition.title,
            "body": rendition.body,
            "tags": rendition.tags,
            "canonical_url": rendition.canonical_url,
            "destination_name": destination.name,
        }
        body_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = compute_hmac_signature(body_bytes, secret, timestamp)
        headers = {
            "Content-Type": "application/json",
            "X-IncuBrix-Timestamp": timestamp,
            "X-IncuBrix-Signature": signature,
            "Idempotency-Key": idempotency_key,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(webhook_url, content=body_bytes, headers=headers)
                if res.status_code not in (200, 201, 202):
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Webhook partner error: {res.text}", status_code=res.status_code)
                data = res.json()
                pid = str(data.get("post_id", f"wh_{idempotency_key[:8]}"))
                live_url = data.get("live_url", f"{webhook_url}/posts/{pid}")
                return PublishResponse(platform_post_id=pid, live_url=live_url, status="live")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))

    async def get_status(
        self,
        platform_post_id: str,
        connection: ConnectionData,
    ) -> GetStatusResponse:
        webhook_url = connection.settings.get("webhook_url", "https://partner.example.com/webhook")
        if settings.SIMULATION_MODE or connection.settings.get("simulation", True):
            return GetStatusResponse(status="live", live_url=f"{webhook_url}/posts/{platform_post_id}")

        secret = connection.credentials.get("signing_secret") or settings.WEBHOOK_SIGNING_SECRET
        timestamp = str(int(time.time()))
        body_bytes = json.dumps({"action": "get_status", "post_id": platform_post_id}).encode()
        sig = compute_hmac_signature(body_bytes, secret, timestamp)
        headers = {
            "Content-Type": "application/json",
            "X-IncuBrix-Timestamp": timestamp,
            "X-IncuBrix-Signature": sig,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{webhook_url}/posts/{platform_post_id}", headers=headers)
                if res.status_code == 404:
                    return GetStatusResponse(status="deleted", live_url="")
                if res.status_code != 200:
                    code = self.map_http_status(res.status_code)
                    raise IncuBrixException(code=code, message=f"Webhook status error: {res.text}")
                data = res.json()
                return GetStatusResponse(
                    status=data.get("status", "live"),
                    live_url=data.get("live_url", f"{webhook_url}/posts/{platform_post_id}"),
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

        webhook_url = connection.settings.get("webhook_url", "")
        secret = connection.credentials.get("signing_secret") or settings.WEBHOOK_SIGNING_SECRET
        timestamp = str(int(time.time()))
        body_bytes = json.dumps({"action": "delete", "post_id": platform_post_id}).encode()
        sig = compute_hmac_signature(body_bytes, secret, timestamp)
        headers = {
            "Content-Type": "application/json",
            "X-IncuBrix-Timestamp": timestamp,
            "X-IncuBrix-Signature": sig,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.delete(f"{webhook_url}/posts/{platform_post_id}", headers=headers)
                if res.status_code in (200, 204, 404):
                    return DeleteResponse(deleted=True)
                code = self.map_http_status(res.status_code)
                raise IncuBrixException(code=code, message=f"Webhook delete error: {res.text}")
        except httpx.RequestError as e:
            raise IncuBrixException(code=ErrorCode.PLATFORM_UNAVAILABLE, message=str(e))
