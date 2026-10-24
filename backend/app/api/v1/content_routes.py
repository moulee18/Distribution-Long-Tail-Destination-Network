from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.entities import ContentItem
from backend.app.schemas.app_schemas import ContentCreate, ContentResponse
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/content", tags=["Content"])

@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    payload: ContentCreate,
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    content = ContentItem(
        title=payload.title,
        body=payload.body,
        canonical_url=payload.canonical_url,
        tags=payload.tags,
        media_urls=payload.media_urls,
        is_promotional=payload.is_promotional,
        contains_ai_content=payload.contains_ai_content,
        ai_disclosure_statement=payload.ai_disclosure_statement,
        language=payload.language,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return content

@router.get("", response_model=List[ContentResponse])
async def list_content(db: AsyncSession = Depends(get_db)):
    stmt = select(ContentItem).order_by(ContentItem.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ContentItem).where(ContentItem.id == content_id)
    res = await db.execute(stmt)
    content = res.scalar_one_or_none()
    if not content:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Content {content_id} not found", 404)
    return content

@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(content_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ContentItem).where(ContentItem.id == content_id)
    res = await db.execute(stmt)
    content = res.scalar_one_or_none()
    if not content:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Content {content_id} not found", 404)
    await db.delete(content)
    await db.commit()
    return None
