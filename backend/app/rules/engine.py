import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.models.entities import Destination, DestinationRule, PublishedPost, PublicationAttempt
from backend.app.schemas.connector_contract import RenditionData

class RuleCheckResult(BaseModel):
    decision: str  # "PASS", "BLOCKED", "RESCHEDULED"
    reasons: List[str] = Field(default_factory=list)
    earliest_eligible_time: Optional[datetime] = None
    requires_assisted: bool = False
    modified_rendition: Optional[RenditionData] = None

class RulesEngine:
    @staticmethod
    def evaluate(
        destination: Destination,
        rule: Optional[DestinationRule],
        rendition: RenditionData,
        last_posted_at: Optional[datetime] = None,
        auto_fix_disclosure: bool = True,
    ) -> RuleCheckResult:
        reasons: List[str] = []
        decision = "PASS"
        earliest_time: Optional[datetime] = None
        requires_assisted = False
        current_rendition = rendition.model_copy(deep=True)

        now = datetime.now(timezone.utc)

        # 1. Automation Permission
        if not destination.automation_allowed:
            requires_assisted = True
            reasons.append("Automated posting is prohibited by community rules. Redirecting to assisted publishing.")

        # 2. Frequency Cap
        # Interval in hours: from rule or derived from destination.frequency_cap
        interval_hours = 24
        if rule and rule.frequency_cap_interval_hours:
            interval_hours = rule.frequency_cap_interval_hours
        elif destination.frequency_cap == "weekly":
            interval_hours = 168
        elif destination.frequency_cap == "biweekly":
            interval_hours = 336
        elif destination.frequency_cap == "monthly":
            interval_hours = 720
        elif destination.frequency_cap == "daily":
            interval_hours = 24

        last_post = last_posted_at or destination.last_posted_at
        if last_post:
            if last_post.tzinfo is None:
                last_post = last_post.replace(tzinfo=timezone.utc)
            cutoff = last_post + timedelta(hours=interval_hours)
            if now < cutoff:
                decision = "RESCHEDULED"
                earliest_time = cutoff
                reasons.append(
                    f"Destination frequency cap of 1 post per {interval_hours}h exceeded. "
                    f"Last posted at {last_post.isoformat()}. Earliest eligible time: {cutoff.isoformat()}."
                )

        # 3. Self-Promotion Policy
        promo_allowed = (
            rule.self_promo_allowed
            if (rule is not None and rule.self_promo_allowed is not None)
            else destination.self_promo_allowed
        )
        if promo_allowed is False and current_rendition.is_promotional:
            decision = "BLOCKED"
            reasons.append("Destination strictly prohibits self-promotional content.")

        # 4. Link Policy
        link_policy = (
            rule.link_policy
            if (rule is not None and rule.link_policy is not None)
            else destination.link_policy
        ) or "allowed"
        has_links = bool(re.search(r'https?://[^\s]+', current_rendition.body)) or bool(re.search(r'\[.+?\]\(https?://.+?\)', current_rendition.body))
        
        if link_policy == "prohibited" and has_links:
            decision = "BLOCKED"
            reasons.append("Destination policy strictly prohibits external links.")
        elif link_policy == "canonical_required" and not current_rendition.canonical_url:
            decision = "BLOCKED"
            reasons.append("Destination requires a canonical URL reference for all syndication.")

        # 5. AI Disclosure Policy
        disclosure_req = (
            rule.disclosure_required
            if (rule is not None and rule.disclosure_required is not None)
            else destination.disclosure_required
        )
        if disclosure_req and current_rendition.contains_ai_content:
            phrase = (rule.disclosure_phrase if (rule and rule.disclosure_phrase) else "Created with AI assistance.")
            has_disclosure = (
                (current_rendition.ai_disclosure_statement and len(current_rendition.ai_disclosure_statement.strip()) > 0)
                or (phrase.lower() in current_rendition.body.lower())
            )
            if not has_disclosure:
                if auto_fix_disclosure:
                    # Authorised auto-insertion
                    current_rendition.ai_disclosure_statement = phrase
                    current_rendition.body = f"{current_rendition.body}\n\n*Note: {phrase}*"
                    reasons.append(f"Mandatory AI disclosure was missing; automatically appended disclosure notice: '{phrase}'.")
                else:
                    decision = "BLOCKED"
                    reasons.append("Destination requires mandatory AI disclosure, but none was provided.")

        # 6. Format Limits Check
        max_title = (rule.title_max_chars if (rule and rule.title_max_chars is not None) else 255)
        max_body = (rule.body_max_chars if (rule and rule.body_max_chars is not None) else 32000)
        if len(current_rendition.title) > max_title:
            decision = "BLOCKED"
            reasons.append(f"Title length ({len(current_rendition.title)}) exceeds maximum permitted ({max_title}).")
        if len(current_rendition.body) > max_body:
            decision = "BLOCKED"
            reasons.append(f"Body length ({len(current_rendition.body)}) exceeds maximum permitted ({max_body}).")

        # 7. Media Type Restrictions
        allowed_media = (rule.allowed_media_types if (rule and rule.allowed_media_types is not None) else [])
        if allowed_media and current_rendition.media_urls:
            # If media URLs are present, check their extensions
            for m in current_rendition.media_urls:
                ext = m.split("?")[0].split(".")[-1].lower()
                allowed_exts = [am.replace("image/", "").replace("video/", "") for am in allowed_media]
                if ext not in allowed_exts:
                    decision = "BLOCKED"
                    reasons.append(f"Media file '{m}' format (.{ext}) is not in destination allowed media types: {allowed_media}.")

        return RuleCheckResult(
            decision=decision,
            reasons=reasons,
            earliest_eligible_time=earliest_time,
            requires_assisted=requires_assisted,
            modified_rendition=current_rendition,
        )

rules_engine = RulesEngine()
