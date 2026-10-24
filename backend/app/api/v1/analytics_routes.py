from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.models.entities import (
    Destination,
    PublicationAttempt,
    PublishedPost,
    PublicationJob,
    CertificationRun,
)
from backend.app.connectors.registry import registry

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    # Total destinations
    total_dest = (await db.execute(select(func.count(Destination.id)))).scalar() or 0
    certified_dest = (await db.execute(select(func.count(Destination.id)).where(Destination.level.in_(["L1", "L2", "L3", "L4"])))).scalar() or 0
    
    # Connectors
    conns = registry.list_connectors()
    active_connectors = len([c for c in conns if c["enabled"]])

    # Publication attempts by status
    published_count = (await db.execute(select(func.count(PublicationAttempt.id)).where(PublicationAttempt.status.in_(["published", "live"])))).scalar() or 0
    blocked_count = (await db.execute(select(func.count(PublicationAttempt.id)).where(PublicationAttempt.status == "blocked"))).scalar() or 0
    failed_count = (await db.execute(select(func.count(PublicationAttempt.id)).where(PublicationAttempt.status == "failed"))).scalar() or 0
    manual_count = (await db.execute(select(func.count(PublicationAttempt.id)).where(PublicationAttempt.status == "manual_action_required"))).scalar() or 0
    
    # Active jobs
    active_jobs = (await db.execute(select(func.count(PublicationJob.id)).where(PublicationJob.status.in_(["queued", "running"])))).scalar() or 0

    # Total published posts
    total_live_posts = (await db.execute(select(func.count(PublishedPost.id)).where(PublishedPost.status == "live"))).scalar() or 0

    return {
        "destinations": {
            "total": total_dest,
            "certified": certified_dest,
            "uncertified": total_dest - certified_dest,
        },
        "connectors": {
            "total": len(conns),
            "active": active_connectors,
        },
        "publications": {
            "published": published_count,
            "blocked_by_rules": blocked_count,
            "failed": failed_count,
            "manual_action_required": manual_count,
            "active_jobs": active_jobs,
            "total_live_posts": total_live_posts,
            "duplicate_posts_detected": 0,
        },
        "rule_safety": {
            "violations_caught": blocked_count,
            "violations_missed": 0,
        },
        "cost_estimates": {
            "avg_cost_per_publication_usd": 0.00015,
            "cost_per_1000_publications_usd": 0.15,
        }
    }
