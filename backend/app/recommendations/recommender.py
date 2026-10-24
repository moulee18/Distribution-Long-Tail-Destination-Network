from typing import List, Tuple
from backend.app.models.entities import Destination, ContentItem
from backend.app.schemas.app_schemas import RecommendationItem

TARGET_AUDIENCES = {"ai", "video", "marketing", "saas", "creators", "founders", "developer", "engineering"}

class DestinationRecommender:
    @staticmethod
    def score_destination(content: ContentItem, destination: Destination) -> Tuple[float, str, bool, List[str], str]:
        ineligibility_reasons: List[str] = []
        eligible = True

        # 1. Rules check: Promotional content
        if content.is_promotional and not destination.self_promo_allowed:
            eligible = False
            ineligibility_reasons.append("Promotional content prohibited by destination policy")

        # 2. Language check
        content_lang = (content.language or "en").lower()
        dest_lang = (destination.language or "en").lower()
        lang_match = (content_lang == dest_lang)
        if not lang_match:
            eligible = False
            ineligibility_reasons.append(f"Language mismatch: content is '{content_lang}', destination is '{dest_lang}'")

        # 3. Tag overlap calculation
        content_tags = set(t.lower() for t in (content.tags or []))
        dest_tags = set(t.lower() for t in (destination.audience_tags or []))
        
        # Intersection with destination audience tags
        overlap = content_tags.intersection(dest_tags)
        # Intersection with target audience focus (AI, video, marketing, SaaS, creators, founders)
        target_focus = dest_tags.intersection(TARGET_AUDIENCES)

        # Baseline score from destination's configured relevance
        base_score = destination.relevance_score or 3.0

        # Adjust score dynamically based on content match
        score = base_score
        if overlap:
            score += min(1.0, len(overlap) * 0.4)
        if target_focus:
            score += min(0.5, len(target_focus) * 0.2)
        if not lang_match:
            score -= 1.5
        if not destination.enabled:
            score = 1.0
            eligible = False
            ineligibility_reasons.append("Destination is currently disabled")

        # Certification level adjustment
        if destination.level in ("L3", "L4"):
            score += 0.3
        elif destination.level == "L0":
            score -= 0.5

        # Clamp between 1.0 and 5.0
        final_score = max(1.0, min(5.0, round(score, 1)))

        # Reason explanation
        reason_parts = []
        if overlap:
            reason_parts.append(f"Content matches audience tags: {', '.join(sorted(overlap))}")
        elif target_focus:
            reason_parts.append(f"Destination aligns with IncuBrix target audience: {', '.join(sorted(target_focus))}")
        else:
            reason_parts.append(f"General audience match in {destination.category or 'tech'}")

        if destination.level in ("L3", "L4"):
            reason_parts.append(f"Certified {destination.level} destination")
        elif destination.level == "L1":
            reason_parts.append("Assisted manual posting required")
        else:
            reason_parts.append("Uncertified destination (L0)")

        reason = ". ".join(reason_parts) + "."

        # Recommended publishing method
        if not eligible:
            recommended_method = "blocked"
        elif not destination.automation_allowed or destination.connector_key == "assisted":
            recommended_method = "assisted_pack"
        else:
            recommended_method = "native_publish"

        return final_score, reason, eligible, ineligibility_reasons, recommended_method

    @classmethod
    def rank_destinations(cls, content: ContentItem, destinations: List[Destination], limit: int = 10) -> List[RecommendationItem]:
        scored_items = []
        for dest in destinations:
            score, reason, eligible, ineligibility_reasons, method = cls.score_destination(content, dest)
            item = RecommendationItem(
                destination_id=dest.id,
                destination_name=dest.name,
                platform_key=dest.platform_key,
                connector_key=dest.connector_key,
                relevance_score=score,
                relevance_reason=reason,
                eligible=eligible,
                ineligibility_reasons=ineligibility_reasons,
                certification_level=dest.level,
                recommended_method=method,
            )
            scored_items.append(item)

        # Sort: eligible first, then by relevance_score descending, then certified level
        scored_items.sort(key=lambda x: (x.eligible, x.relevance_score), reverse=True)
        return scored_items[:limit]

recommender = DestinationRecommender()
