from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import Connection, Connector
from backend.app.schemas.app_schemas import ConnectionCreate, ConnectionResponse
from backend.app.connectors.registry import registry
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/connectors", tags=["Connector Management"])

class ToggleConnectorRequest(BaseModel):
    enabled: bool

@router.get("")
async def list_registered_connectors():
    return registry.list_connectors()

@router.post("/{connector_key}/toggle")
async def toggle_connector_kill_switch(connector_key: str, payload: ToggleConnectorRequest):
    registry.set_enabled(connector_key, payload.enabled)
    return {"connector_key": connector_key, "enabled": payload.enabled}

@router.post("/connections", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(payload: ConnectionCreate, db: AsyncSession = Depends(get_db)):
    conn = Connection(
        destination_id=payload.destination_id,
        connector_key=payload.connector_key,
        encrypted_credentials=payload.credentials,
        settings=payload.settings,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn

@router.get("/connections", response_model=List[ConnectionResponse])
async def list_connections(destination_id: str = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Connection)
    if destination_id:
        stmt = stmt.where(Connection.destination_id == destination_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())
