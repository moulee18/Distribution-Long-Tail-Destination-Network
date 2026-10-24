import asyncio
from celery import Celery
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal
from backend.app.publishing.orchestrator import orchestrator
from backend.app.certification.engine import certification_harness
from backend.app.core.logging import logger

celery_app = Celery(
    "incubrix",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

async def _run_job_async(job_id: str):
    async with AsyncSessionLocal() as session:
        await orchestrator.execute_job(job_id, session)

@celery_app.task(name="tasks.execute_publication_job")
def execute_publication_job(job_id: str):
    logger.info(f"Executing publication job via Celery: {job_id}")
    asyncio.run(_run_job_async(job_id))
    return {"job_id": job_id, "status": "completed"}

@celery_app.task(name="tasks.run_recertification_scheduler")
def run_recertification_scheduler():
    logger.info("Executing periodic recertification task")
    async def _run():
        async with AsyncSessionLocal() as session:
            await certification_harness.run_scheduled_recertification(session)
    asyncio.run(_run())
