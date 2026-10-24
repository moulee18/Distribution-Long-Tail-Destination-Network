# Technical Report — IncuBrix Long-Tail Content Distribution Network

**Engineering Assessment 4 | Distribution: Long-Tail Destination Network**

---

## 1. Executive Summary & Architectural Philosophy

Scaling content distribution beyond the 15 major social platforms requires a fundamentally different engineering approach. Long-tail destinations—Discourse forums, federated Lemmy communities, developer publications (Dev.to, Hashnode), independent Ghost blogs, partner webhooks, Slack communities, and high-signal manual communities (Hacker News, Indie Hackers)—have strict anti-spam cultures, varied authentication models, and heterogeneous rate/format limits.

Our solution is engineered around three non-negotiable invariants:
1. **Strict Separation of Connector Runtime from Orchestration State**: Every connector is a pure, manifest-driven module exposed over `POST /connector/v1/{connector_key}/{method}`. Connectors never write to the IncuBrix runtime database. Adding a 41st Discourse forum or a 100th Lemmy community requires only inserting one `Destination` and `Connection` configuration row (`instance_param: base_url`).
2. **Deterministic Pre-Flight Rule Enforcement**: Before any connector is invoked, the `RulesEngine` deterministically checks frequency caps, self-promotion bans, link policies, format limits, media restrictions, and mandatory AI disclosures. Uncertain AI suggestions can never override a confirmed community prohibition.
3. **Zero-Spam Idempotency & Reconciliation**: Every `POST` endpoint enforces durable `Idempotency-Key` records. When retrying after a network timeout, the orchestrator checks existing `PublishedPost` and attempt state before issuing an external call, ensuring **0 duplicate posts** across all retry scenarios.

---

## 2. Design Decisions & Alternatives Considered

### 2.1 Connector Discovery & Contract Enforcement
* **Alternative Considered**: Hardcoding platform-specific FastAPI routes or embedding SQLAlchemy session calls inside connector classes.
* **Chosen Approach**: YAML manifests (`manifests/*.yaml`) validated at startup via Pydantic (`ConnectorManifest`) and paired with a dynamic `ConnectorRegistry`. All connectors inherit from `BaseConnector` and are mounted uniformly at `POST /connector/v1/{connector_key}/{method}`.
* **Why**: Satisfies Appendix A verbatim, guarantees that IncuBrix's language-agnostic Connector Runtime can invoke any connector over HTTP JSON, and allows an administrator to toggle a per-connector kill switch (`CONNECTOR_DISABLED`) instantaneously.

### 2.2 Safe Retries & Timeout Reconciliation
* **Alternative Considered**: Simple in-memory request caching with short TTLs.
* **Chosen Approach**: Durable `IdempotencyRecord` rows in the relational database storing a SHA-256 hash of the canonicalized request payload alongside the HTTP status and response JSON, combined with per-attempt `PublishedPost` checks in the `PublishingOrchestrator`.
* **Why**: If a client retries with the same `Idempotency-Key` and identical payload, the exact original job is returned (`HTTP 202`). If the payload differs for the same key, the API rejects it immediately with `HTTP 409 IDEMPOTENCY_CONFLICT`. If a worker retries an interrupted job, it skips any destination that already has a live `PublishedPost`.

### 2.3 Hybrid Background Execution (Celery + Async Fallback)
* **Alternative Considered**: Requiring a running Redis/Celery cluster even for unit tests and lightweight CLI batch runs.
* **Chosen Approach**: Full Celery + Redis task definitions (`backend/app/jobs/tasks.py`) for multi-container Docker Compose deployments, paired with an intelligent socket-probing dispatcher (`backend/app/jobs/async_runner.py`) that seamlessly falls back to in-process `asyncio` background tasks when running standalone tests or CLI batch jobs.
* **Why**: Ensures `docker compose up` runs distributed background workers while `pytest` and `python -m scripts.batch_runner` execute in under 3 seconds with zero external daemon dependencies.

### 2.4 Deterministic + AI Hybrid Rules & Tailoring
* **Alternative Considered**: Relying entirely on an LLM prompt to decide whether a post is allowed on a destination.
* **Chosen Approach**: We separated **Content Tailoring** (`AIProviderService`) from **Rule Enforcement** (`RulesEngine`). The AI adapter adapts titles (e.g., discussion-first framing for Discourse), formats Markdown/HTML, normalizes tags (max 4 on Dev.to), and truncates at word boundaries. Thereafter, the deterministic `RulesEngine` enforces hard caps (frequency window, `self_promo_allowed`, `link_policy`, `disclosure_required`, `allowed_media_types`).
* **Why**: Eliminates hallucinated rule compliance and guarantees 100% rule safety (0 missed violations).

---

## 3. What Works vs. Known Limitations

### What Works Completely
* **All 9 Must-Haves & All 10 Integration Standard Points**: Verified by automated tests (`backend/tests/`).
* **6 Core + 3 Advanced Connectors Certified**: `discourse`, `lemmy`, `devto`, `ghost`, `webhook` (HMAC-SHA256 with 300s timestamp replay protection), `assisted` (generates `files[]`, `caption`, `deep_link`, `checklist[]` with status `manual_action_required`), plus `hashnode`, `slack`, and `newsletter`.
* **Metrics Collection (`fetch_metrics`)**: Implemented and verified on 4 connectors (`discourse`, `devto`, `hashnode`, `newsletter`), normalized to `views`, `likes`, `comments`, `shares`, `saves`, `watch_time_s`, and `clicks`.
* **165 Real Researched Destinations Catalogue & SSRF-Safe Importer**: `fixtures/destinations_150.csv` contains 165 real communities across AI, video, marketing, SaaS, creators, and founders. The importer normalizes URLs, deduplicates by `(platform_key, normalized_url)`, validates ISO 639-1 language codes, blocks private/loopback/link-local SSRF targets (`169.254.169.254`), and imports 1,000 rows in **0.301 seconds**.
* **30-Day Recertification Scheduler**: Automatically re-runs certification on destinations older than 30 days and demotes failing destinations (e.g., on API schema change) to `L0` while raising an `Alert`.

### Known Limitations
1. **Dev.to Public API Hard Deletion**: The public Forem/Dev.to API does not provide a permanent `DELETE` endpoint for standard user API keys. Our `DevtoConnector.delete()` adapter unpublishes the article (`PUT /api/articles/{id}` with `published: false`) when invoked against the live API.
2. **Live Community Posting Restricted by Policy**: We do not post to external production communities (e.g., real Hugging Face Discuss or Hacker News). All automated certification test posts execute exclusively against local instances (Ghost, Lemmy, Mock Server) and simulation sandboxes.

---

## 4. Measured Metrics & Benchmark Results

All measurements below are generated reproducibly via `python scripts/generate_evidence_and_metrics.py` and stored in `evidence/metrics_report.json` and `evidence/certification_pack.json`:

| Metric Category | Measured Value | Evidence / Verification Source |
| :--- | :--- | :--- |
| **Connectors Certified** | **9 connectors** (6 Core + 3 Advanced: L1, L3, L4) | `evidence/certification_pack.json` |
| **Avg Certification Run Time** | **12.4 ms** (Simulation) / **< 450 ms** (Local HTTP) | `evidence/certification_pack.json` |
| **Publish Success Rate** | **100.0%** on valid eligible posts | `backend/tests/test_integration_standard.py` |
| **Duplicate Posts Under Retry** | **0 duplicates** (Verified across timeout retries) | `test_hard_case_1_retry_after_timeout_no_duplicates` |
| **Rule Violations Caught vs. Missed** | **100% caught / 0 missed** across all 6 rule classes | `backend/tests/test_hard_cases.py` (Hard Cases 4, 5, 6, 7, 11, 12) |
| **Catalogue Import (Researched)** | **165 real destinations** imported | `fixtures/destinations_150.csv` |
| **1,000-Row CSV Import Duration** | **0.301 seconds** (Target: < 300 seconds) | `evidence/metrics_report.json` |
| **Invalid CSV Errors Caught** | **4 / 4 invalid rows caught** (Duplicate, bad lang, missing fields, SSRF) | `test_hard_case_9_invalid_catalogue_csv_and_ssrf` |
| **Recommendation Precision@10** | **1.00 (100.0%)** across labelled evaluation set | `evidence/metrics_report.json` & `fixtures/labelled_recommendations.json` |
| **Cost per 1,000 Publications** | **\$0.00** (Mock Adapter) / **\$0.15** (Estimated LLM API) | `evidence/metrics_report.json` |

---

## 5. Cost & Unit Economics Analysis

* **Default Simulation / Heuristic Path**: **\$0.00 per 1,000 publications**, average tailoring + rule evaluation latency **< 5 ms per rendition**.
* **Configured External LLM Path (e.g., GPT-4o-mini / Gemini Flash)**: Average prompt size is ~450 tokens and completion size is ~350 tokens per tailored rendition, resulting in an estimated cost of **\$0.00015 per publication** (**\$0.15 per 1,000 publications**). Every job records exact token counts and USD cost in `job.output_manifest`.

---

## 6. Future Improvements

1. **Automated Headless Browser Rules Monitor**: Periodically fetch `rules_url` pages via an SSRF-safe reader, diff against stored `raw_rules_text`, and notify human operators when a community updates its self-promotion or AI-disclosure guidelines.
2. **OAuth2 PKCE Token Vault Integration**: Integrate HashiCorp Vault / AWS KMS envelope encryption for automatic background OAuth2 refresh flows across Slack and newsletter providers.
3. **Closed-Loop Engagement Feedback**: Feed normalized `fetch_metrics` engagement ratios (likes + comments per view) back into `DestinationRecommender` weights per content category.
