# IncuBrix Engineering Assessment 4 — Implementation Status

## Assessment Targets & Verification Tracker

### Must-Haves (Pass / Fail)
- [x] **MH-1**: Exact connector contract (POST /connector/v1/{connector_key}/{method}, manifest, error codes)
- [x] **MH-2**: Six Core connectors certified (Discourse, Lemmy, Dev.to, Ghost, Generic Signed Webhook, Assisted)
- [x] **MH-3**: Configuration, not code (Adding an instance of any connector is a single catalogue/connection row)
- [x] **MH-4**: Rules checked before every post (frequency cap, self-promo, link policy, AI disclosure)
- [x] **MH-5**: Never spam, never cheat (test posts only to test/sandbox, deleted within 10 min, backoff on 429)
- [x] **MH-6**: Safe retries (Idempotency-Key header on POST, timeout-safe retry prevents duplicate posts)
- [x] **MH-7**: Secrets protected & simulation mode (no tokens in logs/repo, simulation mode works with zero keys)
- [x] **MH-8**: Local test instances (Docker Compose up starts services + Lemmy/Ghost/mock platforms)
- [x] **MH-9**: Integration Standard followed & live demo capable

### Integration Standard (20 / 20 marks)
- [x] 1. One-command startup and tests (Docker Compose + single test command, zero paid keys, .env.example)
- [x] 2. Documented HTTP API (OpenAPI 3.1 openapi.yaml, all routes under /api/v1/ and /connector/v1/)
- [x] 3. Background jobs (POST returns 202 with job_id, GET /api/v1/jobs/{id}, HMAC-SHA256 callback)
- [x] 4. Safe retries (Idempotency-Key header on every POST)
- [x] 5. Clear errors (Structured JSON {"error": {"code", "message", "retryable", "details"}})
- [x] 6. Configuration (100% env vars and settings, no hardcoded secrets or machine paths)
- [x] 7. Files in, files out (Uploads or URLs, S3/MinIO compatible storage with download URLs)
- [x] 8. Logs and health (Structured JSON logs with correlation ID and job ID, /health and /ready)
- [x] 9. Output manifest (JSON manifest with provider, model, seed, timing, cost estimate, rights/licence)
- [x] 10. Batch runner (CLI tool `python -m scripts.batch_runner` processing test inputs to output folder)

### Levels
- [x] **Core (Required, 15 marks)**: All 6 Core connectors pass certification run (publish, live URL check, status, delete), stored evidence, shared error code mappings.
- [x] **Advanced (15 marks)**:
  - Catalogue import: CSV validation, normalization, deduplication, reachability (SSRF-protected), row-by-row error reporting, 1,000 rows in <5 min.
  - Rules capture: AI step reads community rules and proposes posting rules for human confirmation.
  - Relevance score (1-5) against IncuBrix's audience with explanation.
  - Tailoring: per-destination format, discussion-first, canonical URLs, word-boundary truncation, hashtags.
  - 3 Advanced connectors: Hashnode, Slack, Newsletter.
- [x] **Outstanding (10 marks)**:
  - Recommender: Rank destinations with transparent scoring, labelled evaluation dataset with measured precision@10.
  - Metrics: fetch_metrics on at least 3 connectors (views, likes, comments, shares, clicks).
  - Recertification scheduler: retests before 30 days, automatic demotion and alerting.
  - Real catalogue: 150+ real, relevant destinations with researched rules and scores.

### Hard Cases (All 12 Scenarios Automated)
1. Publish call times out & retried with same idempotency key (no duplicate post).
2. HTTP 429 response with reset time (backoff & reschedule).
3. Expired token (HTTP 401 mapped to CONNECTION_AUTH_EXPIRED & pause).
4. Title or body longer than destination allows (DEST_SPEC_VIOLATION).
5. Unsupported media format rejected before publishing.
6. Second post inside frequency cap (DEST_RULE_FREQUENCY_CAP).
7. Promotional post to no-promotion community rejected.
8. Platform API schema change triggers certification failure and demotion.
9. Invalid CSV import (duplicates, invalid URLs, mixed invalid languages, row-by-row report).
10. Webhook partner permission revoked (publishing halts).
11. Non-English destination handling (language-aware eligibility & tailoring).
12. Mandatory AI disclosure enforced (auto-insertion or blocking).
