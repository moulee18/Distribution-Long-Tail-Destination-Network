from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status, Request
from backend.app.connectors.registry import registry
from backend.app.schemas.connector_contract import (
    ValidateRequest,
    ValidateResponse,
    PublishRequest,
    PublishResponse,
    GetStatusRequest,
    GetStatusResponse,
    DeleteRequest,
    DeleteResponse,
    FetchMetricsRequest,
    FetchMetricsResponse,
    RefreshAuthRequest,
    RefreshAuthResponse,
    BuildAssistPackRequest,
    BuildAssistPackResponse,
)
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.logging import logger

router = APIRouter(prefix="/connector/v1", tags=["Connector Contract"])

@router.post("/{connector_key}/validate", response_model=ValidateResponse)
async def connector_validate(connector_key: str, payload: ValidateRequest):
    connector = registry.get_connector(connector_key)
    return await connector.validate(payload.rendition, payload.destination, payload.connection)

@router.post("/{connector_key}/publish", response_model=PublishResponse)
async def connector_publish(connector_key: str, payload: PublishRequest):
    connector = registry.get_connector(connector_key)
    return await connector.publish(
        payload.rendition,
        payload.destination,
        payload.connection,
        payload.idempotency_key,
    )

@router.post("/{connector_key}/get_status", response_model=GetStatusResponse)
async def connector_get_status(connector_key: str, payload: GetStatusRequest):
    connector = registry.get_connector(connector_key)
    return await connector.get_status(payload.platform_post_id, payload.connection)

@router.post("/{connector_key}/delete", response_model=DeleteResponse)
async def connector_delete(connector_key: str, payload: DeleteRequest):
    connector = registry.get_connector(connector_key)
    return await connector.delete(payload.platform_post_id, payload.connection)

@router.post("/{connector_key}/fetch_metrics", response_model=FetchMetricsResponse)
async def connector_fetch_metrics(connector_key: str, payload: FetchMetricsRequest):
    connector = registry.get_connector(connector_key)
    return await connector.fetch_metrics(
        payload.platform_post_id,
        payload.connection,
        payload.since,
    )

@router.post("/{connector_key}/refresh_auth", response_model=RefreshAuthResponse)
async def connector_refresh_auth(connector_key: str, payload: RefreshAuthRequest):
    connector = registry.get_connector(connector_key)
    return await connector.refresh_auth(payload.connection)

@router.post("/{connector_key}/build_assist_pack", response_model=BuildAssistPackResponse)
async def connector_build_assist_pack(connector_key: str, payload: BuildAssistPackRequest):
    connector = registry.get_connector(connector_key)
    return await connector.build_assist_pack(payload.rendition, payload.destination)
