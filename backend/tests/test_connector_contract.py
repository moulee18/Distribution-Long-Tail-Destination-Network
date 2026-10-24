import pytest
import httpx

CORE_CONNECTORS = ["discourse", "lemmy", "devto", "ghost", "webhook"]
ADVANCED_CONNECTORS = ["hashnode", "slack", "newsletter"]
METRICS_CONNECTORS = ["discourse", "devto", "hashnode", "newsletter"]

@pytest.mark.asyncio
async def test_all_manifests_loaded(client: httpx.AsyncClient):
    res = await client.get("/api/v1/connectors")
    assert res.status_code == 200
    connectors = res.json()
    keys = {c["key"] for c in connectors}
    for req_key in CORE_CONNECTORS + ["assisted"] + ADVANCED_CONNECTORS:
        assert req_key in keys, f"Connector {req_key} missing from registry"

@pytest.mark.asyncio
@pytest.mark.parametrize("connector_key", CORE_CONNECTORS + ADVANCED_CONNECTORS)
async def test_connector_contract_lifecycle(client: httpx.AsyncClient, connector_key: str):
    """
    Tests Appendix A exact connector contract:
    POST /connector/v1/{connector_key}/validate
    POST /connector/v1/{connector_key}/publish
    POST /connector/v1/{connector_key}/get_status
    POST /connector/v1/{connector_key}/delete
    """
    rendition = {
        "title": f"Contract Test Title for {connector_key}",
        "body": "Contract test body content for automated verification.",
        "tags": ["ai", "saas"],
        "canonical_url": "https://incubrix.com/blog/test",
    }
    destination = {
        "name": f"Test {connector_key} Dest",
        "url": f"https://{connector_key}.example.com",
        "platform_key": connector_key,
        "surface": "post",
        "connector_key": connector_key,
    }
    connection = {
        "credentials": {"api_key": "test_key", "auth_token": "test_token"},
        "settings": {
            "base_url": f"https://{connector_key}.example.com",
            "instance_url": f"https://{connector_key}.example.com",
            "admin_api_url": f"https://{connector_key}.example.com",
            "webhook_url": f"https://{connector_key}.example.com/webhook",
            "simulation": True,
        },
    }

    # 1. Validate
    val_res = await client.post(
        f"/connector/v1/{connector_key}/validate",
        json={"rendition": rendition, "destination": destination, "connection": connection},
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["ok"] is True
    assert val_data["violations"] == []

    # 2. Publish
    pub_res = await client.post(
        f"/connector/v1/{connector_key}/publish",
        json={
            "rendition": rendition,
            "destination": destination,
            "connection": connection,
            "idempotency_key": f"contract_idem_{connector_key}_001",
        },
    )
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert "platform_post_id" in pub_data
    assert "live_url" in pub_data
    assert pub_data["status"] == "live"
    post_id = pub_data["platform_post_id"]

    # 3. Get Status
    stat_res = await client.post(
        f"/connector/v1/{connector_key}/get_status",
        json={"platform_post_id": post_id, "connection": connection},
    )
    assert stat_res.status_code == 200
    stat_data = stat_res.json()
    assert stat_data["status"] == "live"
    assert "live_url" in stat_data

    # 4. Delete
    del_res = await client.post(
        f"/connector/v1/{connector_key}/delete",
        json={"platform_post_id": post_id, "connection": connection},
    )
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["deleted"] is True

@pytest.mark.asyncio
async def test_assisted_connector_contract(client: httpx.AsyncClient):
    """
    Tests Assisted Connector Contract:
    POST /connector/v1/assisted/build_assist_pack
    POST /connector/v1/assisted/publish -> status == manual_action_required
    """
    rendition = {
        "title": "Show HN: IncuBrix Distribution Hub",
        "body": "Rule-respecting community distribution platform.",
        "media_urls": ["https://incubrix.com/media/demo.png"],
        "contains_ai_content": True,
        "ai_disclosure_statement": "Drafted with AI assistance.",
    }
    destination = {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/submit",
        "platform_key": "hn",
        "surface": "manual_submission",
        "connector_key": "assisted",
        "rules_url": "https://news.ycombinator.com/newsguidelines.html",
        "frequency_cap": "monthly",
        "self_promo_allowed": True,
        "disclosure_required": True,
        "automation_allowed": False,
    }

    pack_res = await client.post(
        "/connector/v1/assisted/build_assist_pack",
        json={"rendition": rendition, "destination": destination},
    )
    assert pack_res.status_code == 200
    pack = pack_res.json()
    assert "files" in pack and len(pack["files"]) == 1
    assert "caption" in pack and "Show HN" in pack["caption"]
    assert pack["deep_link"] == "https://news.ycombinator.com/submit"
    assert isinstance(pack["checklist"], list) and len(pack["checklist"]) >= 3

    pub_res = await client.post(
        "/connector/v1/assisted/publish",
        json={
            "rendition": rendition,
            "destination": destination,
            "connection": {"credentials": {}, "settings": {}},
            "idempotency_key": "assist_idem_01",
        },
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "manual_action_required"

@pytest.mark.asyncio
@pytest.mark.parametrize("connector_key", METRICS_CONNECTORS)
async def test_connector_fetch_metrics(client: httpx.AsyncClient, connector_key: str):
    """
    Tests fetch_metrics on at least three connectors (Outstanding level requirement).
    """
    res = await client.post(
        f"/connector/v1/{connector_key}/fetch_metrics",
        json={
            "platform_post_id": f"{connector_key}_test_post_123",
            "connection": {"credentials": {}, "settings": {"simulation": True}},
            "since": "2026-10-01T00:00:00Z",
        },
    )
    assert res.status_code == 200
    data = res.json()
    for field in ["views", "likes", "comments", "shares", "saves", "watch_time_s", "clicks"]:
        assert field in data
        assert isinstance(data[field], int)
    assert data["views"] > 0
