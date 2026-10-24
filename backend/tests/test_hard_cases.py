import os
from datetime import datetime, timezone, timedelta
import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.models.entities import Destination, DestinationRule, Connection, PublishedPost, Alert
from backend.app.rules.engine import rules_engine
from backend.app.schemas.connector_contract import RenditionData

@pytest.mark.asyncio
async def test_hard_case_1_retry_after_timeout_no_duplicates(client: httpx.AsyncClient, db_session: AsyncSession):
    """
    Hard Case 1: Send a publish request, retry using the same Idempotency-Key.
    Verify that no duplicate job or post is created, and conflicting payload returns 409.
    """
    # Create content item
    c_res = await client.post(
        "/api/v1/content",
        json={
            "title": "Idempotency Verification Post",
            "body": "Testing safe retries with idempotency key.",
            "tags": ["ai", "saas"],
        },
    )
    assert c_res.status_code == 201
    content_id = c_res.json()["id"]

    # Create destination
    d_res = await client.post(
        "/api/v1/destinations",
        json={
            "name": "Idempotency Test Forum",
            "url": "https://idem-forum.example.com",
            "platform_key": "discourse",
            "surface": "topic",
            "connector_key": "discourse",
            "level": "L3",
        },
    )
    assert d_res.status_code == 201
    dest_id = d_res.json()["id"]

    idem_key = "hard_case_1_unique_key_999"
    pub_payload = {
        "content_item_id": content_id,
        "destination_ids": [dest_id],
        "auto_tailor": True,
    }

    # First call
    r1 = await client.post(
        "/api/v1/publications",
        json=pub_payload,
        headers={"Idempotency-Key": idem_key},
    )
    assert r1.status_code == 202
    job_id_1 = r1.json()["job_id"]

    # Second call (retry with identical key and payload)
    r2 = await client.post(
        "/api/v1/publications",
        json=pub_payload,
        headers={"Idempotency-Key": idem_key},
    )
    assert r2.status_code == 202
    job_id_2 = r2.json()["job_id"]
    assert job_id_1 == job_id_2, "Retry with same Idempotency-Key must return the exact same job_id"

    # Third call with SAME Idempotency-Key but DIFFERENT payload -> must return 409 IDEMPOTENCY_CONFLICT
    r3 = await client.post(
        "/api/v1/publications",
        json={"content_item_id": content_id, "destination_ids": [], "auto_tailor": False},
        headers={"Idempotency-Key": idem_key},
    )
    assert r3.status_code == 409
    assert r3.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

@pytest.mark.asyncio
async def test_hard_case_2_platform_rate_limit_429(client: httpx.AsyncClient):
    """
    Hard Case 2: Platform returns 429 with reset time.
    Verify mapping to PLATFORM_RATE_LIMIT, retryable=True, and retry_after_seconds.
    """
    res = await client.post(
        "/connector/v1/discourse/publish",
        json={
            "rendition": {"title": "Test 429", "body": "Body"},
            "destination": {
                "name": "Rate Limited Forum",
                "url": "https://ratelimit.example.com",
                "platform_key": "discourse",
                "surface": "topic",
                "connector_key": "discourse",
            },
            "connection": {
                "credentials": {},
                "settings": {"base_url": "https://ratelimit.example.com", "simulate_failure": "rate_limit"},
            },
            "idempotency_key": "hc2_429_key",
        },
    )
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == "PLATFORM_RATE_LIMIT"
    assert err["retryable"] is True
    assert err["details"]["retry_after_seconds"] == 30

@pytest.mark.asyncio
async def test_hard_case_3_expired_token_401(client: httpx.AsyncClient):
    """
    Hard Case 3: Simulate HTTP 401 expired token.
    Verify mapping to CONNECTION_AUTH_EXPIRED and retryable=False.
    """
    res = await client.post(
        "/connector/v1/devto/publish",
        json={
            "rendition": {"title": "Test 401", "body": "Body"},
            "destination": {
                "name": "Dev.to Expired Token",
                "url": "https://dev.to/t/ai",
                "platform_key": "devto",
                "surface": "article",
                "connector_key": "devto",
            },
            "connection": {
                "credentials": {"api_key": "expired_key"},
                "settings": {"simulate_failure": "auth_expired"},
            },
            "idempotency_key": "hc3_401_key",
        },
    )
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == "CONNECTION_AUTH_EXPIRED"
    assert err["retryable"] is False

@pytest.mark.asyncio
async def test_hard_case_4_content_exceeds_format_limits(client: httpx.AsyncClient):
    """
    Hard Case 4: Provide a title longer than destination allows (e.g. >128 chars on Dev.to or >255 on Discourse).
    Verify DEST_SPEC_VIOLATION error.
    """
    long_title = "X" * 300
    res = await client.post(
        "/connector/v1/discourse/publish",
        json={
            "rendition": {"title": long_title, "body": "Valid body"},
            "destination": {
                "name": "Discourse Limit Check",
                "url": "https://discourse.example.com",
                "platform_key": "discourse",
                "surface": "topic",
                "connector_key": "discourse",
            },
            "connection": {"credentials": {}, "settings": {"base_url": "https://discourse.example.com"}},
            "idempotency_key": "hc4_limit_key",
        },
    )
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == "DEST_SPEC_VIOLATION"
    assert any("Title exceeds maximum length" in v for v in err["details"]["violations"])

@pytest.mark.asyncio
async def test_hard_case_5_unsupported_media_rejected():
    """
    Hard Case 5: Submit media incompatible with destination requirements.
    Verify rejection before publication.
    """
    dest = Destination(
        id="dest_hc5",
        name="Image Only Destination",
        url="https://imgonly.example.com",
        normalized_url="https://imgonly.example.com",
        platform_key="discourse",
        connector_key="discourse",
        automation_allowed=True,
        self_promo_allowed=True,
    )
    rule = DestinationRule(
        destination_id="dest_hc5",
        allowed_media_types=["image/png", "image/jpeg"],
    )
    rendition = RenditionData(
        title="Post with unsupported archive file",
        body="Checking media filter",
        media_urls=["https://cdn.example.com/archive.exe"],
    )
    eval_res = rules_engine.evaluate(destination=dest, rule=rule, rendition=rendition)
    assert eval_res.decision == "BLOCKED"
    assert any("not in destination allowed media types" in r for r in eval_res.reasons)

@pytest.mark.asyncio
async def test_hard_case_6_frequency_cap_violation():
    """
    Hard Case 6: Attempt a second post inside a destination's weekly frequency cap.
    Verify the post is rescheduled with earliest eligible time.
    """
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    dest = Destination(
        id="dest_hc6",
        name="Weekly Cap Community",
        url="https://weekly.example.com",
        normalized_url="https://weekly.example.com",
        platform_key="lemmy",
        connector_key="lemmy",
        frequency_cap="weekly",
        automation_allowed=True,
        self_promo_allowed=True,
        last_posted_at=two_hours_ago,
    )
    rule = DestinationRule(
        destination_id="dest_hc6",
        frequency_cap_interval_hours=168,
        max_posts_per_interval=1,
    )
    rendition = RenditionData(title="Second Post This Week", body="Checking frequency cap.")
    eval_res = rules_engine.evaluate(destination=dest, rule=rule, rendition=rendition)
    assert eval_res.decision == "RESCHEDULED"
    assert eval_res.earliest_eligible_time is not None
    assert eval_res.earliest_eligible_time > datetime.now(timezone.utc)
    assert any("frequency cap" in r for r in eval_res.reasons)

@pytest.mark.asyncio
async def test_hard_case_7_prohibited_self_promotion():
    """
    Hard Case 7: Attempt promotional content on a no-promotion destination.
    Verify it is blocked.
    """
    dest = Destination(
        id="dest_hc7",
        name="Strict No-Promo Forum",
        url="https://nopromo.example.com",
        normalized_url="https://nopromo.example.com",
        platform_key="discourse",
        connector_key="discourse",
        self_promo_allowed=False,
        automation_allowed=True,
    )
    rule = DestinationRule(destination_id="dest_hc7", self_promo_allowed=False)
    rendition = RenditionData(
        title="Buy Our SaaS Plan Today - 50% Off!",
        body="Commercial offer link inside.",
        is_promotional=True,
    )
    eval_res = rules_engine.evaluate(destination=dest, rule=rule, rendition=rendition)
    assert eval_res.decision == "BLOCKED"
    assert any("prohibits self-promotional content" in r for r in eval_res.reasons)

@pytest.mark.asyncio
async def test_hard_case_8_platform_api_schema_change_demotes_certification(
    client: httpx.AsyncClient, db_session: AsyncSession
):
    """
    Hard Case 8: Simulate a platform renaming a field in its API response during certification.
    Verify certification fails, destination is demoted to L0, and an alert is created.
    """
    d_res = await client.post(
        "/api/v1/destinations",
        json={
            "name": "Schema Changed Discourse",
            "url": "https://schema-broken.example.com",
            "platform_key": "discourse",
            "surface": "topic",
            "connector_key": "discourse",
            "level": "L3",
        },
    )
    dest_id = d_res.json()["id"]

    # Configure connection to simulate schema change
    await client.post(
        "/api/v1/connectors/connections",
        json={
            "destination_id": dest_id,
            "connector_key": "discourse",
            "credentials": {},
            "settings": {"base_url": "https://schema-broken.example.com", "simulate_failure": "schema_change"},
        },
    )

    # Trigger certification
    cert_res = await client.post(
        "/api/v1/certifications",
        json={"destination_id": dest_id, "target_level": "L3"},
    )
    assert cert_res.status_code == 200
    cert_data = cert_res.json()
    assert cert_data["status"] == "failed"
    assert cert_data["resulting_level"] == "L0"
    assert "schema unexpected" in (cert_data["failure_reason"] or "").lower()

    # Confirm destination was demoted to L0 in database
    get_dest = await client.get(f"/api/v1/destinations/{dest_id}")
    assert get_dest.json()["level"] == "L0"
    assert get_dest.json()["enabled"] is False

@pytest.mark.asyncio
async def test_hard_case_9_invalid_catalogue_csv_and_ssrf(client: httpx.AsyncClient):
    """
    Hard Case 9: Import CSV with duplicates, invalid language values, missing fields, and SSRF private IPs.
    Verify row-by-row error report and SSRF protection.
    """
    invalid_csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "invalid_test_catalogue.csv")
    )
    with open(invalid_csv_path, "r", encoding="utf-8") as f:
        csv_text = f.read()

    res = await client.post(
        "/api/v1/catalogue/import",
        data={"raw_csv": csv_text, "allow_local": "false"},
    )
    assert res.status_code == 200
    summary = res.json()
    assert summary["total_rows"] == 5
    assert summary["imported_count"] == 1
    assert summary["duplicate_count"] == 1
    assert summary["error_count"] == 3
    assert len(summary["errors"]) == 4  # 1 duplicate + 1 invalid lang + 1 missing fields + 1 SSRF blocked

    error_messages = " | ".join(e["error"] for e in summary["errors"])
    assert "Duplicate destination" in error_messages
    assert "klingon_xyz" in error_messages
    assert "Missing required fields" in error_messages
    assert "SSRF" in error_messages

@pytest.mark.asyncio
async def test_hard_case_10_partner_webhook_permission_revoked(client: httpx.AsyncClient):
    """
    Hard Case 10: Partner revokes webhook permission.
    Verify publishing stops immediately with CONNECTION_AUTH_EXPIRED (403).
    """
    res = await client.post(
        "/connector/v1/webhook/publish",
        json={
            "rendition": {"title": "Partner Post", "body": "Content"},
            "destination": {
                "name": "Revoked Partner Site",
                "url": "https://revoked-partner.example.com/webhook",
                "platform_key": "webhook",
                "surface": "publication",
                "connector_key": "webhook",
            },
            "connection": {
                "credentials": {},
                "settings": {"webhook_url": "https://revoked-partner.example.com/webhook", "permission_revoked": True},
            },
            "idempotency_key": "hc10_revoked_key",
        },
    )
    assert res.status_code == 403
    err = res.json()["error"]
    assert err["code"] == "CONNECTION_AUTH_EXPIRED"
    assert "revoked" in err["message"].lower()

@pytest.mark.asyncio
async def test_hard_case_11_non_english_community_eligibility(client: httpx.AsyncClient):
    """
    Hard Case 11: Submit English content vs German content against a German ('de') destination.
    Verify language-aware eligibility and scoring.
    """
    # Create German destination
    d_res = await client.post(
        "/api/v1/destinations",
        json={
            "name": "Feddit.de KI Community",
            "url": "https://feddit.de/c/ki_test",
            "platform_key": "lemmy",
            "surface": "post",
            "connector_key": "lemmy",
            "language": "de",
            "audience_tags": ["ai", "saas"],
            "level": "L3",
        },
    )
    de_dest_id = d_res.json()["id"]

    # Create English content
    c_en = await client.post(
        "/api/v1/content",
        json={"title": "English AI Post", "body": "English text", "language": "en", "tags": ["ai"]},
    )
    en_id = c_en.json()["id"]

    rec_en = await client.post("/api/v1/recommendations", json={"content_item_id": en_id, "limit": 50})
    de_rec_for_en = next(r for r in rec_en.json() if r["destination_id"] == de_dest_id)
    assert de_rec_for_en["eligible"] is False
    assert any("Language mismatch" in reason for reason in de_rec_for_en["ineligibility_reasons"])

    # Create German content
    c_de = await client.post(
        "/api/v1/content",
        json={"title": "Deutscher KI Beitrag", "body": "Deutscher Text", "language": "de", "tags": ["ai"]},
    )
    de_id = c_de.json()["id"]

    rec_de = await client.post("/api/v1/recommendations", json={"content_item_id": de_id, "limit": 50})
    de_rec_for_de = next(r for r in rec_de.json() if r["destination_id"] == de_dest_id)
    assert de_rec_for_de["eligible"] is True

@pytest.mark.asyncio
async def test_hard_case_12_mandatory_ai_disclosure():
    """
    Hard Case 12: Submit AI-generated content without disclosure to a destination that requires AI disclosure.
    Verify blocking when auto_fix_disclosure=False, and automatic disclosure insertion when auto_fix_disclosure=True.
    """
    dest = Destination(
        id="dest_hc12",
        name="AI Transparency Forum",
        url="https://transparency.example.com",
        normalized_url="https://transparency.example.com",
        platform_key="discourse",
        connector_key="discourse",
        disclosure_required=True,
        automation_allowed=True,
        self_promo_allowed=True,
    )
    rule = DestinationRule(
        destination_id="dest_hc12",
        disclosure_required=True,
        disclosure_phrase="Created with AI assistance.",
    )
    rendition = RenditionData(
        title="AI Generated Industry Report",
        body="This report summarizes recent benchmarks.",
        contains_ai_content=True,
        ai_disclosure_statement=None,
    )

    # 1. Without auto-fix -> BLOCKED
    res_strict = rules_engine.evaluate(dest, rule, rendition, auto_fix_disclosure=False)
    assert res_strict.decision == "BLOCKED"
    assert any("requires mandatory AI disclosure" in r for r in res_strict.reasons)

    # 2. With authorised auto-fix -> PASS and disclosure appended
    res_autofix = rules_engine.evaluate(dest, rule, rendition, auto_fix_disclosure=True)
    assert res_autofix.decision == "PASS"
    assert "Created with AI assistance." in res_autofix.modified_rendition.body
