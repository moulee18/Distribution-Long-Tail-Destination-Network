from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Input Schemas for Connector Contract (Appendix A)

class RenditionData(BaseModel):
    title: str = Field(..., description="Post title or headline")
    body: str = Field(..., description="Body content (markdown, text or html)")
    excerpt: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    canonical_url: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_promotional: bool = Field(default=False)
    contains_ai_content: bool = Field(default=False)
    ai_disclosure_statement: Optional[str] = Field(default=None)

class DestinationData(BaseModel):
    name: str
    url: str
    platform_key: str
    surface: str
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
    last_certified_at: Optional[str] = None

class ConnectionData(BaseModel):
    credentials: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)

# Method Request Payloads

class ValidateRequest(BaseModel):
    rendition: RenditionData
    destination: DestinationData
    connection: ConnectionData

class PublishRequest(BaseModel):
    rendition: RenditionData
    destination: DestinationData
    connection: ConnectionData
    idempotency_key: str

class GetStatusRequest(BaseModel):
    platform_post_id: str
    connection: ConnectionData

class DeleteRequest(BaseModel):
    platform_post_id: str
    connection: ConnectionData

class FetchMetricsRequest(BaseModel):
    platform_post_id: str
    connection: ConnectionData
    since: Optional[str] = None

class RefreshAuthRequest(BaseModel):
    connection: ConnectionData

class BuildAssistPackRequest(BaseModel):
    rendition: RenditionData
    destination: DestinationData

# Method Response Payloads

class ValidateResponse(BaseModel):
    ok: bool
    violations: List[str] = Field(default_factory=list)

class PublishResponse(BaseModel):
    platform_post_id: str
    live_url: str
    status: str

class GetStatusResponse(BaseModel):
    status: str
    live_url: str

class DeleteResponse(BaseModel):
    deleted: bool

class FetchMetricsResponse(BaseModel):
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    watch_time_s: int = 0
    clicks: int = 0

class RefreshAuthResponse(BaseModel):
    expires_at: str

class AssistPackFile(BaseModel):
    name: str
    url: str
    type: str

class BuildAssistPackResponse(BaseModel):
    files: List[AssistPackFile] = Field(default_factory=list)
    caption: str
    deep_link: str
    checklist: List[str] = Field(default_factory=list)
