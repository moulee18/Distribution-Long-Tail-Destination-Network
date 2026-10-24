from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import ContentItem, Destination
from backend.app.schemas.app_schemas import RecommendationRequest, RecommendationItem
from backend.app.recommendations.recommender import recommender
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.post("", response_model=List[RecommendationItem])
async def get_recommendations(payload: RecommendationRequest, db: AsyncSession = Depends(get_db)):
    c_stmt = select(ContentItem).where(ContentItem.id == payload.content_item_id)
    c_res = await db.execute(c_stmt)
    content = c_res.scalar_one_or_none()
    if not content:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Content {payload.content_item_id} not found", 404)

    d_stmt = select(Destination)
    d_res = await db.execute(d_stmt)
    destinations = list(d_res.scalars().all())

    ranked = recommender.rank_destinations(content, destinations, limit=payload.limit)
    return ranked
