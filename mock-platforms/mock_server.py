import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

mock_app = FastAPI(title="IncuBrix Mock Platforms Server", version="1.0.0")

# In-memory storage for mock posts
MOCK_DISCOURSE_POSTS: Dict[str, Dict] = {}
MOCK_LEMMY_POSTS: Dict[str, Dict] = {}
MOCK_DEVTO_ARTICLES: Dict[str, Dict] = {}
MOCK_GHOST_POSTS: Dict[str, Dict] = {}
MOCK_WEBHOOK_DELIVERIES: Dict[str, Dict] = {}

WEBHOOK_PARTNER_REVOKED = False

# Helper for failure simulation
def check_simulation_header(request: Request):
    fail = request.headers.get("X-Simulate-Failure") or request.query_params.get("simulate_failure")
    if fail == "rate_limit":
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Try again in 30 seconds."},
            headers={"Retry-After": "30"},
        )
    if fail == "auth_expired":
        return JSONResponse(status_code=401, content={"error": "Token expired or revoked."})
    if fail == "content_rejected":
        return JSONResponse(status_code=422, content={"error": "Content rejected by moderation filter."})
    if fail == "server_error":
        return JSONResponse(status_code=500, content={"error": "Internal platform error."})
    if fail == "schema_change":
        # Renamed field in API response!
        return JSONResponse(status_code=200, content={"status_unknown_weird_key": 9999})
    return None

# 1. Discourse Mocks
@mock_app.post("/posts.json")
async def mock_discourse_create_post(request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    body = await request.json()
    post_id = str(len(MOCK_DISCOURSE_POSTS) + 100)
    topic_id = 42
    MOCK_DISCOURSE_POSTS[post_id] = {
        "id": int(post_id),
        "topic_id": topic_id,
        "topic_slug": "test-topic",
        "raw": body.get("raw"),
        "title": body.get("title"),
        "created_at": time.time(),
    }
    return {
        "id": int(post_id),
        "topic_id": topic_id,
        "topic_slug": "test-topic",
    }

@mock_app.get("/posts/{post_id}.json")
async def mock_discourse_get_post(post_id: str, request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    post = MOCK_DISCOURSE_POSTS.get(post_id)
    if not post:
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return post

@mock_app.delete("/posts/{post_id}.json")
async def mock_discourse_delete_post(post_id: str, request: Request):
    if post_id in MOCK_DISCOURSE_POSTS:
        del MOCK_DISCOURSE_POSTS[post_id]
    return {"success": "OK"}

# 2. Lemmy Mocks
@mock_app.post("/api/v3/post")
async def mock_lemmy_create_post(request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    body = await request.json()
    pid = len(MOCK_LEMMY_POSTS) + 1
    post_data = {
        "id": pid,
        "name": body.get("name"),
        "body": body.get("body"),
        "deleted": False,
    }
    MOCK_LEMMY_POSTS[str(pid)] = post_data
    return {"post_view": {"post": post_data}}

@mock_app.get("/api/v3/post")
async def mock_lemmy_get_post(id: str, request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    post = MOCK_LEMMY_POSTS.get(str(id))
    if not post:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"post_view": {"post": post}}

@mock_app.post("/api/v3/post/delete")
async def mock_lemmy_delete_post(request: Request):
    body = await request.json()
    pid = str(body.get("post_id"))
    if pid in MOCK_LEMMY_POSTS:
        MOCK_LEMMY_POSTS[pid]["deleted"] = True
    return {"post_view": {"post": MOCK_LEMMY_POSTS.get(pid, {"deleted": True})}}

# 3. Dev.to Mocks
@mock_app.post("/api/articles")
async def mock_devto_create_article(request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    body = await request.json()
    article = body.get("article", {})
    aid = len(MOCK_DEVTO_ARTICLES) + 1
    data = {
        "id": aid,
        "title": article.get("title"),
        "body_markdown": article.get("body_markdown"),
        "published": article.get("published", True),
        "url": f"http://localhost:8001/articles/{aid}",
        "page_views_count": 150,
        "positive_reactions_count": 12,
        "comments_count": 3,
    }
    MOCK_DEVTO_ARTICLES[str(aid)] = data
    return JSONResponse(status_code=201, content=data)

@mock_app.get("/api/articles/{article_id}")
async def mock_devto_get_article(article_id: str, request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    art = MOCK_DEVTO_ARTICLES.get(article_id)
    if not art:
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return art

@mock_app.put("/api/articles/{article_id}")
async def mock_devto_update_article(article_id: str, request: Request):
    art = MOCK_DEVTO_ARTICLES.get(article_id)
    if not art:
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    body = await request.json()
    art["published"] = body.get("article", {}).get("published", art["published"])
    return art

# 4. Ghost Mocks
@mock_app.post("/ghost/api/admin/posts/")
async def mock_ghost_create_post(request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    body = await request.json()
    posts = body.get("posts", [{}])
    p = posts[0]
    pid = f"ghost_{len(MOCK_GHOST_POSTS)+1}"
    post_data = {
        "id": pid,
        "title": p.get("title"),
        "html": p.get("html"),
        "status": p.get("status", "published"),
        "url": f"http://localhost:8001/p/{pid}/",
    }
    MOCK_GHOST_POSTS[pid] = post_data
    return JSONResponse(status_code=201, content={"posts": [post_data]})

@mock_app.get("/ghost/api/admin/posts/{post_id}/")
async def mock_ghost_get_post(post_id: str, request: Request):
    sim = check_simulation_header(request)
    if sim:
        return sim
    p = MOCK_GHOST_POSTS.get(post_id)
    if not p:
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return {"posts": [p]}

@mock_app.delete("/ghost/api/admin/posts/{post_id}/")
async def mock_ghost_delete_post(post_id: str, request: Request):
    if post_id in MOCK_GHOST_POSTS:
        del MOCK_GHOST_POSTS[post_id]
    return Response(status_code=204)

# 5. Partner Webhook Receiver (HMAC-SHA256 Signed)
@mock_app.post("/mock/webhook/receiver")
async def mock_webhook_receiver(
    request: Request,
    x_incubrix_timestamp: Optional[str] = Header(None),
    x_incubrix_signature: Optional[str] = Header(None),
):
    global WEBHOOK_PARTNER_REVOKED
    if WEBHOOK_PARTNER_REVOKED:
        return JSONResponse(status_code=403, content={"error": "Partner permission has been revoked."})

    sim = check_simulation_header(request)
    if sim:
        return sim

    body_bytes = await request.body()
    if not x_incubrix_timestamp or not x_incubrix_signature:
        return JSONResponse(status_code=401, content={"error": "Missing signature headers."})

    # Timestamp replay protection: reject if older than 300 seconds
    now = int(time.time())
    try:
        ts = int(x_incubrix_timestamp)
        if abs(now - ts) > 300:
            return JSONResponse(status_code=400, content={"error": "Request timestamp expired (replay protection)."})
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid timestamp format."})

    # Verify HMAC-SHA256
    secret = "incubrix-default-webhook-signing-secret"
    expected = hmac.new(secret.encode(), f"{x_incubrix_timestamp}.".encode() + body_bytes, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_incubrix_signature):
        return JSONResponse(status_code=401, content={"error": "Invalid HMAC signature."})

    data = json.loads(body_bytes.decode())
    pid = f"wh_{int(time.time()*1000)}"
    MOCK_WEBHOOK_DELIVERIES[pid] = data
    return JSONResponse(
        status_code=200,
        content={"status": "accepted", "post_id": pid, "live_url": f"http://localhost:8001/mock/webhook/posts/{pid}"},
    )

@mock_app.post("/mock/webhook/partner/revoke")
async def mock_revoke_partner():
    global WEBHOOK_PARTNER_REVOKED
    WEBHOOK_PARTNER_REVOKED = True
    return {"partner_revoked": True}

@mock_app.post("/mock/webhook/partner/restore")
async def mock_restore_partner():
    global WEBHOOK_PARTNER_REVOKED
    WEBHOOK_PARTNER_REVOKED = False
    return {"partner_revoked": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8001)
