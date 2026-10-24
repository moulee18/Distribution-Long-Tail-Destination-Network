from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Content Schemas

class ContentCreate(BaseModel):
    title: str = Field(..., max_length=500)
    body: str
    canonical_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    is_promotional: bool = False
    contains_ai_content: bool = False
    ai_disclosure_statement: Optional[str] = None
    language: str = "en"

class ContentResponse(BaseModel):
    id: str
    title: str
    body: str
    canonical_url: Optional[str] = None
    tags: List[str]
    media_urls: List[str]
    is_promotional: bool
    contains_ai_content: bool
    ai_disclosure_statement: Optional[str] = None
    language: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Destination & Rule Schemas

class DestinationRuleSchema(BaseModel):
    frequency_cap_interval_hours: int = 24
    max_posts_per_interval: int = 1
    self_promo_allowed: bool = True
    promo_tag_required: bool = False
    link_policy: str = "allowed"
    disclosure_required: bool = False
    disclosure_phrase: str = "Created with AI assistance."
    title_max_chars: int = 255
    body_max_chars: int = 32000
    allowed_media_types: List[str] = Field(default_factory=list)
    human_confirmed: bool = True
    raw_rules_text: Optional[str] = None

class DestinationCreate(BaseModel):
    name: str
    url: str
    platform_key: str
    surface: str = "post"
    category: Optional[str] = None
    audience_tags: List[str] = Field(default_factory=list)
    language: str = "en"
    geo: str = "GLOBAL"
    est_audience: int = 0
    rules_url: Optional[str] = None
    frequency_cap: str = "daily"
    self_promo_allowed: bool = True
    link_policy: str = "allowed"
    disclosure_required: bool = False
    automation_allowed: bool = True
    connector_key: str
    relevance_score: float = 3.0
    relevance_reason: Optional[str] = None
    level: str = "L0"
    rules: Optional[DestinationRuleSchema] = None

class DestinationResponse(BaseModel):
    id: str
    name: str
    url: str
    normalized_url: str
    platform_key: str
    surface: str
    category: Optional[str] = None
    audience_tags: List[str]
    language: str
    geo: str
    est_audience: int
    rules_url: Optional[str] = None
    frequency_cap: str
    self_promo_allowed: bool
    link_policy: str
    disclosure_required: bool
    automation_allowed: bool
    connector_key: str
    relevance_score: float
    relevance_reason: Optional[str] = None
    level: str
    last_certified_at: Optional[datetime] = None
    enabled: bool
    last_posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    rules: Optional[DestinationRuleSchema] = None

    model_config = ConfigDict(from_attributes=True)

# Connection Schemas

class ConnectionCreate(BaseModel):
    destination_id: str
    connector_key: str
    credentials: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)

class ConnectionResponse(BaseModel):
    id: str
    destination_id: str
    connector_key: str
    settings: Dict[str, Any]
    auth_expired: bool
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Publication and Job Schemas

class PublicationRequest(BaseModel):
    content_item_id: str
    destination_ids: List[str]
    auto_tailor: bool = True
    callback_url: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    total_destinations: int
    completed_destinations: int
    callback_url: Optional[str] = None
    error_summary: Optional[str] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)
    output_manifest: Dict[str, Any] = Field(default_factory=dict)

# Certification Schemas

class CertificationTriggerRequest(BaseModel):
    destination_id: str
    target_level: str = "L3"  # L1, L2, L3, L4

class CertificationResponse(BaseModel):
    id: str
    destination_id: str
    connector_key: str
    status: str
    tested_level: str
    resulting_level: str
    failure_reason: Optional[str] = None
    cleanup_status: str
    platform_post_id: Optional[str] = None
    live_url: Optional[str] = None
    duration_ms: int
    created_at: datetime
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Recommendations

class RecommendationRequest(BaseModel):
    content_item_id: str
    limit: int = 10

class RecommendationItem(BaseModel):
    destination_id: str
    destination_name: str
    platform_key: str
    connector_key: str
    relevance_score: float
    relevance_reason: str
    eligible: bool
    ineligibility_reasons: List[str] = Field(default_factory=list)
    certification_level: str
    recommended_method: str  # native_publish | assisted_pack | blocked

# Catalogue Import

class ImportSummary(BaseModel):
    total_rows: int
    imported_count: int
    duplicate_count: int
    error_count: int
    duration_seconds: float
    errors: List[Dict[str, Any]] = Field(default_factory=list)
