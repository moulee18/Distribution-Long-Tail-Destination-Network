import hashlib
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import (
    PublicationJob,
    PublicationAttempt,
    PublishedPost,
    IdempotencyRecord,
    ContentItem,
    Destination,
)
from backend.app.schemas.app_schemas import PublicationRequest, JobResponse
from backend.app.jobs.async_runner import dispatch_job
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.logging import logger

router = APIRouter(prefix="/publications", tags=["Publications"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_publication(
    payload: PublicationRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    # Hash payload for idempotency verification
    payload_str = json.dumps(payload.model_dump(), sort_keys=True)
    payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    if idempotency_key:
        stmt_idem = select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
        res_idem = await db.execute(stmt_idem)
        existing_idem = res_idem.scalar_one_or_none()

        if existing_idem:
            if existing_idem.request_hash == payload_hash:
                # Same key, identical payload -> return stored response
                logger.info(f"Idempotent request recognized for key {idempotency_key}; returning existing job.")
                resp_data = existing_idem.response_body
                return JobResponse(**resp_data)
            else:
                # Same key, differing payload -> IDEMPOTENCY CONFLICT
                raise IncuBrixException(
                    code=ErrorCode.IDEMPOTENCY_CONFLICT,
                    message=f"Idempotency conflict: key '{idempotency_key}' was previously used with a different request payload.",
                    status_code=status.HTTP_409_CONFLICT,
                )

    # Validate content item existence
    c_stmt = select(ContentItem).where(ContentItem.id == payload.content_item_id)
    c_res = await db.execute(c_stmt)
    if not c_res.scalar_one_or_none():
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Content {payload.content_item_id} not found", 404)

    # Create publication job
    job = PublicationJob(
        content_item_id=payload.content_item_id,
        status="queued",
        progress=0,
        callback_url=payload.callback_url,
        total_destinations=len(payload.destination_ids),
        idempotency_key=idempotency_key,
    )
    db.add(job)
    await db.flush()

    # Create publication attempts
    for dest_id in payload.destination_ids:
        attempt = PublicationAttempt(
            job_id=job.id,
            destination_id=dest_id,
            status="queued",
        )
        db.add(attempt)

    # Record idempotency
    response_dto = JobResponse(
        job_id=job.id,
        status="queued",
        progress=0,
        total_destinations=len(payload.destination_ids),
        completed_destinations=0,
        callback_url=payload.callback_url,
        results=[],
    )

    if idempotency_key:
        idem_rec = IdempotencyRecord(
            idempotency_key=idempotency_key,
            request_hash=payload_hash,
            status="COMPLETED",
            status_code=202,
            response_body=response_dto.model_dump(),
        )
        db.add(idem_rec)

    await db.commit()
    await db.refresh(job)

    # Dispatch to background runner
    dispatch_job(job.id)

    return response_dto

@router.get("/history")
async def get_publication_history(
    destination_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(PublicationAttempt, Destination.name.label("destination_name"), ContentItem.title.label("content_title"))
        .join(Destination, PublicationAttempt.destination_id == Destination.id)
        .join(PublicationJob, PublicationAttempt.job_id == PublicationJob.id)
        .join(ContentItem, PublicationJob.content_item_id == ContentItem.id)
        .order_by(PublicationAttempt.created_at.desc())
    )
    if destination_id:
        stmt = stmt.where(PublicationAttempt.destination_id == destination_id)

    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for attempt, dest_name, content_title in rows[:limit]:
        items.append({
            "attempt_id": attempt.id,
            "job_id": attempt.job_id,
            "destination_id": attempt.destination_id,
            "destination_name": dest_name,
            "content_title": content_title,
            "status": attempt.status,
            "rule_decision": attempt.rule_decision,
            "rule_reasons": attempt.rule_reasons,
            "platform_post_id": attempt.platform_post_id,
            "live_url": attempt.live_url,
            "error_code": attempt.error_code,
            "error_message": attempt.error_message,
            "scheduled_for": attempt.scheduled_for.isoformat() if attempt.scheduled_for else None,
            "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
        })
    return items
