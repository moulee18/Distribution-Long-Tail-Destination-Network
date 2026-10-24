# IncuBrix Distribution Hub — Long-Tail Content Distribution Network

**Engineering Assessment 4 | Long-Tail Distribution**

IncuBrix Distribution Hub is an intelligent, rule-respecting long-tail content syndication platform. It enables creators to submit one piece of content and distribute it across hundreds of forums, open fediverse communities, developer blogs, newsletters, Slack workspaces, partner websites, and manual-only communities while strictly enforcing each destination's posting rules and format limits.

---

## 1. Architecture Overview

**Core Philosophy: One Connector, Many Destinations.**
Adding a 41st Discourse forum or a 20th Lemmy community requires only a single catalogue/connection configuration row—zero new connector code.

```text
Frontend SaaS Dashboard (/ui)
       │
       ▼
FastAPI Application (/api/v1/* & /connector/v1/*)
       ├── Authentication, Correlation-ID & Redacted JSON Logging Middleware
       ├── Destination Catalogue & SSRF-Safe CSV Importer (165+ Researched Sites)
       ├── AI Content Tailoring Adapter (Swappable Mock / LLM Provider)
       ├── Destination Recommendation Engine (Precision@10 = 1.00 on Labelled Set)
       ├── Deterministic Posting-Rules Engine (Freq Cap, Self-Promo, Links, AI Disclosure)
       ├── Publishing Orchestrator & Durable Idempotency Engine (PostgreSQL / SQLite)
       ├── Background Job Queue (Celery + Redis / Async Task Runner + HMAC Callbacks)
       ├── Automated Certification Harness (Validate → Publish → Status → Delete → Evidence)
       └── Reusable Connector Runtime (POST /connector/v1/{connector_key}/{method})
             ├── Core: discourse | lemmy | devto | ghost | webhook (HMAC) | assisted
             └── Advanced: hashnode | slack | newsletter
```

---

## 2. Quick Start (Under 10 Commands)

### Option A: One-Command Docker Compose Startup (Full Stack + Local Ghost, Lemmy & Mock Servers)
```bash
cp .env.example .env
docker compose up --build -d
```

### Option B: Standalone Local Python Startup (Zero External Daemons Required)
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

* **Web Application UI**: `http://localhost:8000/ui/index.html` (or `http://localhost:8000/`)
* **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
* **Health & Readiness Checks**: `http://localhost:8000/health` and `http://localhost:8000/ready`

---

## 3. Running Tests, Batch Runner & Evidence Generation

All tests run deterministically with **no paid API keys required**:

```bash
# 1. Run full automated test suite (32 tests: Contract, 12 Hard Cases, Integration Standard, E2E)
pytest backend/tests -v

# 2. Run Integration Standard CLI Batch Runner
python -m scripts.batch_runner --input fixtures/batch_inputs --output evidence/batch_outputs

# 3. Generate Certification Evidence Pack & Measured Metrics Report
python scripts/generate_evidence_and_metrics.py
```

---

## 4. Shared Error Codes (Appendix A & Integration Standard Point 5)

All errors follow the structured JSON format:
```json
{
  "error": {
    "code": "PLATFORM_RATE_LIMIT",
    "message": "Discourse rate limit reached (429)",
    "retryable": true,
    "details": {
      "retry_after_seconds": 30
    }
  }
}
```

| Code | Retryable | Meaning & Expected Action |
| :--- | :---: | :--- |
| `DEST_SPEC_VIOLATION` | `false` | Content breaks destination's format limits (title/body length, media, tags); returns field-level violations. |
| `DEST_RULE_FREQUENCY_CAP` | `true` | Frequency cap reached; rescheduled to `earliest_eligible_time` after the cap window. |
| `CONNECTION_AUTH_EXPIRED` | `false` | Token expired, invalid (HTTP 401/403), or partner revoked permission; pauses destination until reconnected. |
| `PLATFORM_RATE_LIMIT` | `true` | HTTP 429 received; backs off using the platform's `Retry-After` / reset time. |
| `PLATFORM_QUOTA_EXHAUSTED` | `true` | Daily platform quota exhausted; reschedules for next window. |
| `PLATFORM_CONTENT_REJECTED` | `false` | Platform moderation or schema rejected content (HTTP 400/422); returns message for review. |
| `PLATFORM_UNAVAILABLE` | `true` | Upstream 5xx or network timeout; retries with backoff and trips circuit breaker after 5 consecutive failures. |
| `CONNECTOR_DISABLED` | `false` | Administrator kill switch is active for this connector. |
| `IDEMPOTENCY_CONFLICT` | `false` | Same `Idempotency-Key` reused with a different request payload (HTTP 409). |
| `RESOURCE_NOT_FOUND` | `false` | Requested entity ID does not exist (HTTP 404). |
| `VALIDATION_ERROR` | `false` | Request input or CSV row failed validation (HTTP 400/409). |

---

## 5. Configuration Settings (`.env.example`)

All settings are loaded via environment variables (`backend/app/core/config.py`):
* `SIMULATION_MODE`: `true` (default) uses deterministic simulation adapters with zero external accounts; `false` sends live HTTP calls to configured instances.
* `DATABASE_URL` / `DATABASE_URL_SYNC`: PostgreSQL (`postgresql+asyncpg://...`) in Docker Compose or SQLite (`sqlite+aiosqlite:///...`) in standalone mode.
* `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`: Redis endpoints for Celery workers.
* `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` / `MINIO_BUCKET_NAME`: S3-compatible object storage with automatic local disk fallback.
* `WEBHOOK_SIGNING_SECRET`: HMAC-SHA256 secret used to sign outbound partner webhooks and job completion callbacks.
* `AI_PROVIDER` / `AI_MODEL_NAME` / `AI_API_KEY`: Swappable AI tailoring provider (`mock` default).

---

## 6. Known Limitations

1. **Dev.to Public API Deletion**: The public Forem/Dev.to v1 API does not expose a hard `DELETE /api/articles/{id}` endpoint for standard API keys. Our `devto` connector implements an adapter that unpublishes the article (`PUT /api/articles/{id}` with `published: false`) during cleanup and documents this behaviour transparently.
2. **External Production Communities**: In accordance with Assessment Rule *"Never spam, never cheat"*, all 165 real communities in `fixtures/destinations_150.csv` are catalogued for rules, relevance scoring, and recommendation only; automated test posts are strictly restricted to local instances and sandboxes.
