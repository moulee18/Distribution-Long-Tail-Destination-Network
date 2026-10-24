import asyncio
import json
import os
import time
import pytest
import httpx

from backend.app.core.logging import redact_secrets

@pytest.mark.asyncio
async def test_health_and_ready_endpoints(client: httpx.AsyncClient):
    """
    Integration Standard Point 8: GET /health and GET /ready endpoints, plus X-Correlation-Id.
    """
    h_res = await client.get("/health", headers={"X-Correlation-Id": "test-corr-12345"})
    assert h_res.status_code == 200
    assert h_res.headers.get("X-Correlation-Id") == "test-corr-12345"
    assert h_res.json()["status"] == "healthy"

    r_res = await client.get("/ready")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["status"] == "ready"
    assert r_data["checks"]["database"] is True
    assert r_data["checks"]["connectors"] is True

def test_secret_redaction_in_logs():
    """
    Must-Have 7 & Integration Standard: Tokens and API keys must never appear in logs.
    """
    raw_log = 'Failed request with api_key="sk_live_9876543210secret" and Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
    safe_log = redact_secrets(raw_log)
    assert "sk_live_9876543210secret" not in safe_log
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in safe_log
    assert "***REDACTED***" in safe_log

@pytest.mark.asyncio
async def test_connector_kill_switch(client: httpx.AsyncClient):
    """
    Shared Error Code: CONNECTOR_DISABLED when kill switch is active.
    """
    # Disable slack connector
    t_res = await client.post("/api/v1/connectors/slack/toggle", json={"enabled": False})
    assert t_res.status_code == 200

    # Attempt validate on disabled connector
    v_res = await client.post(
        "/connector/v1/slack/validate",
        json={
            "rendition": {"title": "Test", "body": "Body"},
            "destination": {
                "name": "Slack Test",
                "url": "https://slack.com",
                "platform_key": "slack",
                "surface": "message",
                "connector_key": "slack",
            },
            "connection": {"credentials": {}, "settings": {}},
        },
    )
    assert v_res.status_code == 403
    assert v_res.json()["error"]["code"] == "CONNECTOR_DISABLED"

    # Re-enable slack connector
    await client.post("/api/v1/connectors/slack/toggle", json={"enabled": True})

@pytest.mark.asyncio
async def test_end_to_end_publishing_job_and_manifest(client: httpx.AsyncClient):
    """
    Integration Standard Points 3, 4, 9:
    POST /api/v1/publications returns 202 with job_id.
    GET /api/v1/jobs/{job_id} returns status, progress 0-100, results, and output_manifest.
    """
    c_res = await client.post(
        "/api/v1/content",
        json={
            "title": "End-to-End Syndication Guide for AI Video Creators",
            "body": "Learn how to distribute long-tail content across forums and developer blogs.",
            "canonical_url": "https://incubrix.com/blog/e2e-guide",
            "tags": ["ai", "video", "creators", "saas"],
            "contains_ai_content": True,
        },
    )
    content_id = c_res.json()["id"]

    d1 = await client.post(
        "/api/v1/destinations",
        json={
            "name": "E2E Discourse Forum",
            "url": "https://e2e-discourse.example.com",
            "platform_key": "discourse",
            "surface": "topic",
            "connector_key": "discourse",
            "disclosure_required": True,
            "level": "L3",
        },
    )
    d2 = await client.post(
        "/api/v1/destinations",
        json={
            "name": "E2E Assisted Community",
            "url": "https://e2e-assisted.example.com/submit",
            "platform_key": "hn",
            "surface": "manual_submission",
            "connector_key": "assisted",
            "automation_allowed": False,
            "level": "L1",
        },
    )
    dest_ids = [d1.json()["id"], d2.json()["id"]]

    pub_res = await client.post(
        "/api/v1/publications",
        json={"content_item_id": content_id, "destination_ids": dest_ids, "auto_tailor": True},
        headers={"Idempotency-Key": "e2e_test_job_key_001"},
    )
    assert pub_res.status_code == 202
    job_id = pub_res.json()["job_id"]

    # Wait briefly for async task completion
    for _ in range(20):
        j_res = await client.get(f"/api/v1/jobs/{job_id}")
        job_data = j_res.json()
        if job_data["status"] in ("succeeded", "failed", "partial"):
            break
        await asyncio.sleep(0.1)

    assert job_data["status"] == "succeeded"
    assert job_data["progress"] == 100
    assert len(job_data["results"]) == 2

    statuses = {r["destination_name"]: r["status"] for r in job_data["results"]}
    assert statuses["E2E Discourse Forum"] == "published"
    assert statuses["E2E Assisted Community"] == "manual_action_required"

    # Verify Output Manifest (Integration Standard Point 9)
    manifest = job_data["output_manifest"]
    assert "incubrix_version" in manifest
    assert "ai_provider" in manifest
    assert "cost_usd" in manifest["ai_provider"]
    assert "licence_rights" in manifest
    assert manifest["licence_rights"]["commercial_usable"] is True

@pytest.mark.asyncio
async def test_six_core_connectors_certification(client: httpx.AsyncClient):
    """
    Must-Have 2 & Core Level:
    Every Core connector (discourse, lemmy, devto, ghost, webhook, assisted) passes full certification
    (validate, publish, get_status, delete/cleanup) with stored evidence.
    """
    core_configs = [
        ("Cert Discourse", "https://cert-discourse.example.com", "discourse", "discourse", "L4"),
        ("Cert Lemmy", "https://cert-lemmy.example.com", "lemmy", "lemmy", "L3"),
        ("Cert Dev.to", "https://dev.to/t/certtest", "devto", "devto", "L4"),
        ("Cert Ghost", "https://cert-ghost.example.com", "ghost", "ghost", "L3"),
        ("Cert Webhook", "https://cert-webhook.example.com/hook", "webhook", "webhook", "L3"),
        ("Cert Assisted", "https://cert-assisted.example.com/submit", "hn", "assisted", "L1"),
    ]

    for name, url, p_key, c_key, target_lvl in core_configs:
        d_res = await client.post(
            "/api/v1/destinations",
            json={
                "name": name,
                "url": url,
                "platform_key": p_key,
                "surface": "post",
                "connector_key": c_key,
                "automation_allowed": (c_key != "assisted"),
            },
        )
        dest_id = d_res.json()["id"]

        cert_res = await client.post(
            "/api/v1/certifications",
            json={"destination_id": dest_id, "target_level": target_lvl},
        )
        assert cert_res.status_code == 200
        c_data = cert_res.json()
        assert c_data["status"] == "success", f"Certification failed for {c_key}: {c_data}"
        assert c_data["resulting_level"] == target_lvl
        assert len(c_data["evidence"]) >= 2
        if c_key != "assisted":
            assert c_data["cleanup_status"] == "deleted"

@pytest.mark.asyncio
async def test_1000_row_catalogue_import_performance_and_precision_at_10(client: httpx.AsyncClient):
    """
    Advanced & Outstanding Level Verification:
    1. Import the 165 real destinations + synthetic rows up to 1,000 rows in well under 5 minutes.
    2. Evaluate Recommendation Precision@10 against the labelled evaluation dataset.
    """
    # Seed the 165 real researched destinations first
    seed_res = await client.post("/api/v1/catalogue/seed-full")
    assert seed_res.status_code == 200
    seed_summary = seed_res.json()
    assert seed_summary["imported_count"] >= 150

    # Evaluate Precision@10 on labelled evaluation dataset
    eval_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "labelled_recommendations.json")
    )
    with open(eval_path, "r", encoding="utf-8") as f:
        eval_queries = json.load(f)

    precisions = []
    for q in eval_queries:
        c_res = await client.post("/api/v1/content", json=q["content"])
        cid = c_res.json()["id"]
        rec_res = await client.post("/api/v1/recommendations", json={"content_item_id": cid, "limit": 10})
        top_10 = rec_res.json()
        assert len(top_10) == 10

        # Check how many of top 10 are eligible and meet the ground truth criteria
        hits = 0
        for item in top_10:
            if item["eligible"] and item["relevance_score"] >= q["min_expected_relevance_score"]:
                hits += 1
        precisions.append(hits / 10.0)

    avg_precision_at_10 = sum(precisions) / len(precisions)
    assert avg_precision_at_10 >= 0.8, f"Expected Precision@10 >= 0.80, got {avg_precision_at_10}"

    # Also test 1,000-row CSV import speed (< 5 minutes required; should take < 5 seconds)
    lines = ["name,url,platform_key,surface,category,audience_tags,language,geo,est_audience,rules_url,frequency_cap,self_promo_allowed,link_policy,disclosure_required,automation_allowed,connector_key,relevance_score,relevance_reason,level,last_certified_at"]
    for i in range(1000):
        lines.append(
            f"Perf Forum {i},https://perf-forum-{i}.example.org,discourse,topic,AI,ai;saas,en,GLOBAL,5000,https://perf-forum-{i}.example.org/rules,weekly,true,allowed,false,true,discourse,4.2,Perf test row,L3,"
        )
    csv_1000 = "\n".join(lines)

    t0 = time.time()
    imp_res = await client.post("/api/v1/catalogue/import", data={"raw_csv": csv_1000, "allow_local": "true"})
    elapsed = time.time() - t0
    assert imp_res.status_code == 200
    imp_data = imp_res.json()
    assert imp_data["imported_count"] == 1000
    assert elapsed < 300.0, f"1,000 rows took {elapsed}s (must be < 300s)"
