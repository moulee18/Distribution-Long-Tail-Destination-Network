from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.app.core.database import get_db
from backend.app.models.entities import Destination, DestinationRule
from backend.app.schemas.app_schemas import (
    DestinationCreate,
    DestinationResponse,
    DestinationRuleSchema,
)
from backend.app.services.catalogue import normalize_url, is_safe_external_url
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/destinations", tags=["Destinations"])

class ProposeRulesRequest(BaseModel):
    rules_url: Optional[str] = None
    raw_rules_text: Optional[str] = None

class ProposeRulesResponse(BaseModel):
    proposed_rules: DestinationRuleSchema
    explanation: str

@router.post("", response_model=DestinationResponse, status_code=status.HTTP_201_CREATED)
async def create_destination(payload: DestinationCreate, db: AsyncSession = Depends(get_db)):
    norm_url = normalize_url(payload.url)
    
    # Duplicate check
    stmt = select(Destination).where(
        Destination.platform_key == payload.platform_key,
        Destination.normalized_url == norm_url,
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise IncuBrixException(
            ErrorCode.VALIDATION_ERROR,
            f"Destination with platform {payload.platform_key} and URL {norm_url} already exists",
            409,
        )

    dest = Destination(
        name=payload.name,
        url=payload.url,
        normalized_url=norm_url,
        platform_key=payload.platform_key,
        surface=payload.surface,
        category=payload.category,
        audience_tags=[t.lower() for t in payload.audience_tags],
        language=payload.language.lower(),
        geo=payload.geo,
        est_audience=payload.est_audience,
        rules_url=payload.rules_url,
        frequency_cap=payload.frequency_cap,
        self_promo_allowed=payload.self_promo_allowed,
        link_policy=payload.link_policy,
        disclosure_required=payload.disclosure_required,
        automation_allowed=payload.automation_allowed,
        connector_key=payload.connector_key,
        relevance_score=payload.relevance_score,
        relevance_reason=payload.relevance_reason,
        level=payload.level,
    )
    db.add(dest)
    await db.flush()

    # Create associated rule
    rule_data = payload.rules or DestinationRuleSchema()
    rule = DestinationRule(
        destination_id=dest.id,
        frequency_cap_interval_hours=rule_data.frequency_cap_interval_hours,
        max_posts_per_interval=rule_data.max_posts_per_interval,
        self_promo_allowed=rule_data.self_promo_allowed,
        promo_tag_required=rule_data.promo_tag_required,
        link_policy=rule_data.link_policy,
        disclosure_required=rule_data.disclosure_required,
        disclosure_phrase=rule_data.disclosure_phrase,
        title_max_chars=rule_data.title_max_chars,
        body_max_chars=rule_data.body_max_chars,
        allowed_media_types=rule_data.allowed_media_types,
        human_confirmed=rule_data.human_confirmed,
        raw_rules_text=rule_data.raw_rules_text,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(dest)
    return dest

@router.get("", response_model=List[DestinationResponse])
async def list_destinations(
    platform: Optional[str] = None,
    level: Optional[str] = None,
    language: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Destination).order_by(Destination.relevance_score.desc(), Destination.created_at.desc())
    if platform:
        stmt = stmt.where(Destination.platform_key == platform)
    if level:
        stmt = stmt.where(Destination.level == level)
    if language:
        stmt = stmt.where(Destination.language == language)
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(or_(Destination.name.ilike(search_filter), Destination.url.ilike(search_filter)))

    res = await db.execute(stmt)
    dests = list(res.scalars().all())

    if tag:
        tag_lower = tag.lower()
        dests = [d for d in dests if tag_lower in [t.lower() for t in (d.audience_tags or [])]]

    return dests[:limit]

@router.get("/{destination_id}", response_model=DestinationResponse)
async def get_destination(destination_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(stmt)
    dest = res.scalar_one_or_none()
    if not dest:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Destination {destination_id} not found", 404)
    return dest

@router.put("/{destination_id}", response_model=DestinationResponse)
async def update_destination(destination_id: str, payload: DestinationCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(stmt)
    dest = res.scalar_one_or_none()
    if not dest:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Destination {destination_id} not found", 404)

    dest.name = payload.name
    dest.url = payload.url
    dest.normalized_url = normalize_url(payload.url)
    dest.platform_key = payload.platform_key
    dest.surface = payload.surface
    dest.category = payload.category
    dest.audience_tags = [t.lower() for t in payload.audience_tags]
    dest.language = payload.language.lower()
    dest.geo = payload.geo
    dest.est_audience = payload.est_audience
    dest.rules_url = payload.rules_url
    dest.frequency_cap = payload.frequency_cap
    dest.self_promo_allowed = payload.self_promo_allowed
    dest.link_policy = payload.link_policy
    dest.disclosure_required = payload.disclosure_required
    dest.automation_allowed = payload.automation_allowed
    dest.connector_key = payload.connector_key
    dest.relevance_score = payload.relevance_score
    dest.relevance_reason = payload.relevance_reason

    await db.commit()
    await db.refresh(dest)
    return dest

@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_destination(destination_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Destination).where(Destination.id == destination_id)
    res = await db.execute(stmt)
    dest = res.scalar_one_or_none()
    if not dest:
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"Destination {destination_id} not found", 404)
    await db.delete(dest)
    await db.commit()
    return None

@router.post("/ai-propose-rules", response_model=ProposeRulesResponse)
async def propose_rules_from_text(payload: ProposeRulesRequest):
    """
    AI step: parses community guidelines / rules text and proposes structured posting rules.
    A human confirms before the rules are active.
    """
    text = (payload.raw_rules_text or "").lower()
    
    # Heuristics + mock AI extraction
    no_promo = "no self promotion" in text or "no advertising" in text or "no promo" in text or "no spam" in text
    needs_disclosure = "ai" in text and ("disclose" in text or "disclosure" in text or "transparency" in text)
    no_links = "no links" in text or "direct text only" in text
    
    proposed = DestinationRuleSchema(
        frequency_cap_interval_hours=168 if ("weekly" in text or "once a week" in text) else 24,
        max_posts_per_interval=1,
        self_promo_allowed=not no_promo,
        promo_tag_required="promo tag" in text or "flair" in text,
        link_policy="prohibited" if no_links else ("canonical_required" if "canonical" in text else "allowed"),
        disclosure_required=needs_disclosure,
        disclosure_phrase="Content generated with AI assistance." if needs_disclosure else "",
        title_max_chars=200 if "short title" in text else 255,
        body_max_chars=32000,
        human_confirmed=False,  # Needs human confirmation!
        raw_rules_text=payload.raw_rules_text,
    )
    explanation = (
        f"AI analysis detected: Self-promotion {'PROHIBITED' if no_promo else 'ALLOWED'}; "
        f"AI Disclosure {'REQUIRED' if needs_disclosure else 'OPTIONAL'}; "
        f"Links policy '{proposed.link_policy}'."
    )
    return ProposeRulesResponse(proposed_rules=proposed, explanation=explanation)
