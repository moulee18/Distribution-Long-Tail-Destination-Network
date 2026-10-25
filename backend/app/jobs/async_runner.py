import asyncio
import socket
from urllib.parse import urlparse
from backend.app.jobs.tasks import celery_app, _run_job_async
from backend.app.core.config import settings
from backend.app.core.logging import logger

def _is_redis_reachable() -> bool:
    try:
        parsed = urlparse(settings.CELERY_BROKER_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except Exception:
        return False

def dispatch_job(job_id: str):
    if _is_redis_reachable():
        try:
            celery_app.send_task("tasks.execute_publication_job", args=[job_id])
            logger.info(f"Dispatched job {job_id} to Celery broker")
            return
        except Exception as e:
            logger.warning(f"Celery send_task failed ({str(e)}), falling back to local asyncio task")
    asyncio.create_task(_run_job_async(job_id))
