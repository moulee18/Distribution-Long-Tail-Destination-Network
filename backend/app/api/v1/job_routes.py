from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import PublicationJob, PublicationAttempt, Destination
from backend.app.schemas.app_schemas import JobResponse
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(PublicationJob).where(PublicationJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Job {job_id} not found", 404)

    # Fetch attempts
    stmt_a = (
        select(PublicationAttempt, Destination.name.label("dest_name"), Destination.url.label("dest_url"))
        .join(Destination, PublicationAttempt.destination_id == Destination.id)
        .where(PublicationAttempt.job_id == job_id)
    )
    res_a = await db.execute(stmt_a)
    attempts_data = res_a.all()

    results: List[Dict[str, Any]] = []
    for attempt, dest_name, dest_url in attempts_data:
        results.append({
            "attempt_id": attempt.id,
            "destination_id": attempt.destination_id,
            "destination_name": dest_name,
            "status": attempt.status,
            "rule_decision": attempt.rule_decision,
            "rule_reasons": attempt.rule_reasons,
            "platform_post_id": attempt.platform_post_id,
            "live_url": attempt.live_url,
            "assist_pack": attempt.assist_pack,
            "error_code": attempt.error_code,
            "error_message": attempt.error_message,
        })

    return JobResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        total_destinations=job.total_destinations,
        completed_destinations=job.completed_destinations,
        callback_url=job.callback_url,
        error_summary=job.error_summary,
        results=results,
        output_manifest=job.output_manifest or {},
    )
