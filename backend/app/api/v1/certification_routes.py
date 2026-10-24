from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import CertificationRun, CertificationEvidence, Destination
from backend.app.schemas.app_schemas import CertificationTriggerRequest, CertificationResponse
from backend.app.certification.engine import certification_harness
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/certifications", tags=["Certification Engine"])

@router.post("", response_model=CertificationResponse)
async def trigger_certification(payload: CertificationTriggerRequest, db: AsyncSession = Depends(get_db)):
    run = await certification_harness.certify_destination(
        destination_id=payload.destination_id,
        target_level=payload.target_level,
        db=db,
    )
    # Fetch evidence for response
    ev_stmt = select(CertificationEvidence).where(CertificationEvidence.run_id == run.id)
    ev_res = await db.execute(ev_stmt)
    ev_records = ev_res.scalars().all()

    evidence_list = [
        {
            "step": e.step,
            "request_data": e.request_data,
            "response_data": e.response_data,
            "status_code": e.status_code,
        }
        for e in ev_records
    ]

    return CertificationResponse(
        id=run.id,
        destination_id=run.destination_id,
        connector_key=run.connector_key,
        status=run.status,
        tested_level=run.tested_level,
        resulting_level=run.resulting_level,
        failure_reason=run.failure_reason,
        cleanup_status=run.cleanup_status,
        platform_post_id=run.platform_post_id,
        live_url=run.live_url,
        duration_ms=run.duration_ms,
        created_at=run.created_at,
        evidence=evidence_list,
    )

@router.get("", response_model=List[CertificationResponse])
async def list_certification_runs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(CertificationRun).order_by(CertificationRun.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    runs = res.scalars().all()
    
    result = []
    for r in runs:
        ev_stmt = select(CertificationEvidence).where(CertificationEvidence.run_id == r.id)
        ev_res = await db.execute(ev_stmt)
        ev_records = ev_res.scalars().all()
        evidence_list = [
            {
                "step": e.step,
                "request_data": e.request_data,
                "response_data": e.response_data,
                "status_code": e.status_code,
            }
            for e in ev_records
        ]
        result.append(
            CertificationResponse(
                id=r.id,
                destination_id=r.destination_id,
                connector_key=r.connector_key,
                status=r.status,
                tested_level=r.tested_level,
                resulting_level=r.resulting_level,
                failure_reason=r.failure_reason,
                cleanup_status=r.cleanup_status,
                platform_post_id=r.platform_post_id,
                live_url=r.live_url,
                duration_ms=r.duration_ms,
                created_at=r.created_at,
                evidence=evidence_list,
            )
        )
    return result

@router.post("/scheduler/run")
async def trigger_recertification_scheduler(db: AsyncSession = Depends(get_db)):
    runs = await certification_harness.run_scheduled_recertification(db)
    return {"message": f"Recertification completed for {len(runs)} destinations", "run_ids": [r.id for r in runs]}
