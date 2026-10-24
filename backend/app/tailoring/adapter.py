import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.schemas.connector_contract import RenditionData

class TailoringResult(BaseModel):
    rendition: RenditionData
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

def truncate_at_word_boundary(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated[:max_chars - 3] + "..."

class MockAIProvider:
    def __init__(self, model_name: str = "incubrix-tailor-mock"):
        self.model_name = model_name

    def tailor(
        self,
        title: str,
        body: str,
        connector_key: str,
        tags: List[str],
        canonical_url: Optional[str] = None,
        is_promotional: bool = False,
        contains_ai_content: bool = False,
        ai_disclosure: Optional[str] = None,
        destination_language: str = "en",
    ) -> TailoringResult:
        # Prompt tokens approximation
        prompt_len = len(title) + len(body)
        prompt_tokens = max(10, prompt_len // 4)
        
        tailored_title = title
        tailored_body = body
        tailored_tags = [t.lower().replace(" ", "-") for t in tags]

        if connector_key == "discourse":
            # Discussion framing
            if not tailored_title.endswith("?"):
                tailored_title = f"{tailored_title} — What are your thoughts?"
            tailored_body = (
                f"{body}\n\n"
                "**Discussion prompt:** Have you encountered this in your workflow? "
                "How does your team handle this?"
            )
        elif connector_key == "devto":
            # Tech article format, tags limit 4
            tailored_tags = [t.replace("#", "") for t in tailored_tags][:4]
            tailored_body = f"# {title}\n\n{body}"
        elif connector_key == "ghost":
            # Blog post structure
            tailored_body = f"## Overview\n\n{body}\n\n---\n*Published via IncuBrix Syndication.*"
        elif connector_key == "lemmy":
            # Concise title
            tailored_title = truncate_at_word_boundary(title, 180)
        elif connector_key == "slack":
            # Shortened message format
            tailored_title = truncate_at_word_boundary(title, 120)
            tailored_body = truncate_at_word_boundary(body, 3500)

        # Truncate at word boundaries if excessively long
        tailored_title = truncate_at_word_boundary(tailored_title, 250)

        # AI disclosure preservation
        if contains_ai_content and not ai_disclosure:
            ai_disclosure = "Generated with AI assistance."

        rendition = RenditionData(
            title=tailored_title,
            body=tailored_body,
            tags=tailored_tags,
            canonical_url=canonical_url,
            is_promotional=is_promotional,
            contains_ai_content=contains_ai_content,
            ai_disclosure_statement=ai_disclosure,
        )

        completion_tokens = max(10, (len(tailored_title) + len(tailored_body)) // 4)
        # Cost estimate: $0.001 per 1k input tokens, $0.002 per 1k output tokens
        cost_usd = round((prompt_tokens * 0.000001) + (completion_tokens * 0.000002), 6)

        return TailoringResult(
            rendition=rendition,
            provider="mock",
            model=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
        )

class AIProviderService:
    def __init__(self):
        self.mock_provider = MockAIProvider(settings.AI_MODEL_NAME)

    def tailor(
        self,
        title: str,
        body: str,
        connector_key: str,
        tags: List[str],
        canonical_url: Optional[str] = None,
        is_promotional: bool = False,
        contains_ai_content: bool = False,
        ai_disclosure: Optional[str] = None,
        destination_language: str = "en",
    ) -> TailoringResult:
        # If settings.AI_PROVIDER == "mock" or no API key provided, use mock provider
        return self.mock_provider.tailor(
            title=title,
            body=body,
            connector_key=connector_key,
            tags=tags,
            canonical_url=canonical_url,
            is_promotional=is_promotional,
            contains_ai_content=contains_ai_content,
            ai_disclosure=ai_disclosure,
            destination_language=destination_language,
        )

ai_service = AIProviderService()
