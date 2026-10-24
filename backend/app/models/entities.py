import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(50), default="creator")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class ContentItem(Base):
    __tablename__ = "content_items"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    canonical_url = Column(String(1000), nullable=True)
    tags = Column(JSON, default=list)  # list of str
    media_urls = Column(JSON, default=list)  # list of str
    is_promotional = Column(Boolean, default=False)
    contains_ai_content = Column(Boolean, default=False)
    ai_disclosure_statement = Column(String(1000), nullable=True)
    language = Column(String(10), default="en")
    status = Column(String(50), default="draft")  # draft, ready, publishing, published
    author_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    renditions = relationship("ContentRendition", back_populates="content_item", cascade="all, delete-orphan")
    assets = relationship("ContentAsset", back_populates="content_item", cascade="all, delete-orphan")

class ContentAsset(Base):
    __tablename__ = "content_assets"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    content_item_id = Column(String(36), ForeignKey("content_items.id"), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)  # image, video, file
    file_path = Column(String(1000), nullable=False)  # S3 or MinIO key / local path
    url = Column(String(1000), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    content_item = relationship("ContentItem", back_populates="assets")

class Destination(Base):
    __tablename__ = "destinations"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    normalized_url = Column(String(1000), nullable=False, index=True)
    platform_key = Column(String(50), nullable=False, index=True)  # discourse, lemmy, devto, ghost, webhook, assisted, hashnode, slack, newsletter
    surface = Column(String(100), nullable=False, default="post")
    category = Column(String(100), nullable=True)
    audience_tags = Column(JSON, default=list)  # e.g. ["saas", "ai", "marketing"]
    language = Column(String(10), default="en")
    geo = Column(String(50), default="GLOBAL")
    est_audience = Column(Integer, default=0)
    rules_url = Column(String(1000), nullable=True)
    
    # Posting rules snapshot
    frequency_cap = Column(String(50), default="daily")  # e.g. daily, weekly, biweekly, monthly
    self_promo_allowed = Column(Boolean, default=True)
    link_policy = Column(String(50), default="allowed")  # allowed, prohibited, limited_promo, canonical_required
    disclosure_required = Column(Boolean, default=False)
    automation_allowed = Column(Boolean, default=True)
    
    connector_key = Column(String(50), nullable=False, index=True)
    relevance_score = Column(Float, default=3.0)  # 1 to 5
    relevance_reason = Column(Text, nullable=True)
    level = Column(String(10), default="L0")  # L0, L1, L2, L3, L4
    last_certified_at = Column(DateTime(timezone=True), nullable=True)
    
    enabled = Column(Boolean, default=True)
    last_posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("platform_key", "normalized_url", name="uq_dest_platform_url"),
    )

    rules = relationship("DestinationRule", back_populates="destination", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="destination", lazy="selectin", cascade="all, delete-orphan")

class DestinationRule(Base):
    __tablename__ = "destination_rules"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=False, unique=True, index=True)
    frequency_cap_interval_hours = Column(Integer, default=24)  # e.g. 24 for daily, 168 for weekly
    max_posts_per_interval = Column(Integer, default=1)
    self_promo_allowed = Column(Boolean, default=True)
    promo_tag_required = Column(Boolean, default=False)
    link_policy = Column(String(50), default="allowed")
    disclosure_required = Column(Boolean, default=False)
    disclosure_phrase = Column(String(255), default="Created with AI assistance.")
    title_max_chars = Column(Integer, default=255)
    body_max_chars = Column(Integer, default=32000)
    allowed_media_types = Column(JSON, default=list)
    human_confirmed = Column(Boolean, default=True)
    raw_rules_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    destination = relationship("Destination", back_populates="rules")

class Connector(Base):
    __tablename__ = "connectors"
    key = Column(String(50), primary_key=True)  # discourse, lemmy, devto, ghost, webhook, assisted, etc.
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    tier = Column(String(50), nullable=False)  # native, protocol, bridge, feed, assisted
    auth_type = Column(String(50), nullable=False)  # api_key, oauth2, bot_token, none
    capabilities = Column(JSON, default=list)  # publish, status, delete, metrics, build_assist_pack
    rate_limits = Column(JSON, default=dict)
    instance_param = Column(String(100), default="none")
    enabled = Column(Boolean, default=True)  # kill switch
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class Connection(Base):
    __tablename__ = "connections"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=False, index=True)
    connector_key = Column(String(50), ForeignKey("connectors.key"), nullable=False)
    encrypted_credentials = Column(JSON, default=dict)  # auth tokens, keys (encrypted)
    settings = Column(JSON, default=dict)  # platform instance url, category/channel/tag ids
    auth_expired = Column(Boolean, default=False)
    consecutive_failures = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    destination = relationship("Destination", back_populates="connections")

class ContentRendition(Base):
    __tablename__ = "content_renditions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    content_item_id = Column(String(36), ForeignKey("content_items.id"), nullable=False, index=True)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=True, index=True)
    connector_key = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    excerpt = Column(String(1000), nullable=True)
    tags = Column(JSON, default=list)
    media_urls = Column(JSON, default=list)
    canonical_url = Column(String(1000), nullable=True)
    metadata_fields = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    content_item = relationship("ContentItem", back_populates="renditions")

class PublicationJob(Base):
    __tablename__ = "publication_jobs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    content_item_id = Column(String(36), ForeignKey("content_items.id"), nullable=False, index=True)
    status = Column(String(50), default="queued")  # queued, running, succeeded, failed, partial
    progress = Column(Integer, default=0)  # 0 to 100
    callback_url = Column(String(1000), nullable=True)
    total_destinations = Column(Integer, default=0)
    completed_destinations = Column(Integer, default=0)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    error_summary = Column(Text, nullable=True)
    output_manifest = Column(JSON, default=dict)  # Integration Standard manifest
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    attempts = relationship("PublicationAttempt", back_populates="job", cascade="all, delete-orphan")

class PublicationAttempt(Base):
    __tablename__ = "publication_attempts"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    job_id = Column(String(36), ForeignKey("publication_jobs.id"), nullable=False, index=True)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=False, index=True)
    rendition_id = Column(String(36), ForeignKey("content_renditions.id"), nullable=True)
    status = Column(String(50), default="queued")
    # Statuses: draft, validation_pending, blocked, queued, running, published,
    # verification_failed, manual_action_required, retry_scheduled, failed, deleted
    rule_decision = Column(String(50), nullable=True)  # PASS, BLOCKED, RESCHEDULED
    rule_reasons = Column(JSON, default=list)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, default=0)
    platform_post_id = Column(String(255), nullable=True, index=True)
    live_url = Column(String(1000), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    assist_pack = Column(JSON, default=dict)  # For assisted tier
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    job = relationship("PublicationJob", back_populates="attempts")
    destination = relationship("Destination")
    post = relationship("PublishedPost", back_populates="attempt", uselist=False)

class PublishedPost(Base):
    __tablename__ = "published_posts"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    attempt_id = Column(String(36), ForeignKey("publication_attempts.id"), nullable=False, unique=True)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=False, index=True)
    platform_post_id = Column(String(255), nullable=False, index=True)
    live_url = Column(String(1000), nullable=True)
    status = Column(String(50), default="live")  # live, deleted, unpublished
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    attempt = relationship("PublicationAttempt", back_populates="post")

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)  # SHA-256 of normalized request body
    status = Column(String(50), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class CertificationRun(Base):
    __tablename__ = "certification_runs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=False, index=True)
    connector_key = Column(String(50), nullable=False)
    status = Column(String(50), default="running")  # running, success, failed
    tested_level = Column(String(10), default="L3")  # L1, L2, L3, L4
    resulting_level = Column(String(10), default="L0")
    failure_reason = Column(Text, nullable=True)
    cleanup_status = Column(String(50), default="pending")  # pending, deleted, failed, preserved_sandbox
    platform_post_id = Column(String(255), nullable=True)
    live_url = Column(String(1000), nullable=True)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    destination = relationship("Destination")
    evidence = relationship("CertificationEvidence", back_populates="run", cascade="all, delete-orphan")

class CertificationEvidence(Base):
    __tablename__ = "certification_evidence"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    run_id = Column(String(36), ForeignKey("certification_runs.id"), nullable=False, index=True)
    step = Column(String(100), nullable=False)  # validate, publish, check_status, delete, metrics
    request_data = Column(JSON, default=dict)
    response_data = Column(JSON, default=dict)
    status_code = Column(Integer, nullable=True)
    evidence_file_path = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    run = relationship("CertificationRun", back_populates="evidence")

class DestinationMetrics(Base):
    __tablename__ = "destination_metrics"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    destination_id = Column(String(36), ForeignKey("destinations.id"), nullable=False, index=True)
    platform_post_id = Column(String(255), nullable=False, index=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    watch_time_s = Column(Integer, default=0)
    raw_metrics = Column(JSON, default=dict)
    collected_at = Column(DateTime(timezone=True), default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    user_id = Column(String(36), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class ProviderUsage(Base):
    __tablename__ = "provider_usage"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    severity = Column(String(50), default="warning")  # info, warning, error, critical
    source = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
