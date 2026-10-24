# Submission Form Evidence Mapping Guide

Use this reference table to populate every tab of the IncuBrix Assessment 4 Excel Submission Form. Every item is backed by concrete files, automated tests, and generated evidence JSON packs.

---

## Tab 1: Must-Haves (All 9 Pass)

| # | Must-Have | Status | Evidence File / Endpoint | Automated Test Reference | Explanation |
| :- | :--- | :---: | :--- | :--- | :--- |
| **1** | Exact connector contract (`POST /connector/v1/{connector_key}/{method}`, manifest, error codes) | **Yes** | `backend/app/api/connector_routes.py`, `manifests/*.yaml`, `backend/app/core/errors.py` | `backend/tests/test_connector_contract.py` (`test_connector_contract_lifecycle`) | Exposes exact `validate`, `publish`, `get_status`, `delete`, `fetch_metrics`, `refresh_auth`, `build_assist_pack` routes and shared error codes. |
| **2** | Six Core connectors certified (Discourse, Lemmy, Dev.to, Ghost, Signed Webhook, Assisted) | **Yes** | `evidence/certification_pack.json`, `backend/app/connectors/*` | `test_six_core_connectors_certification` & `test_assisted_connector_contract` | All 6 Core connectors pass full certification (`validate` → `publish` → `get_status` → `delete`) with stored step-by-step evidence. |
| **3** | Configuration, not code (Adding another forum/site is one catalogue row) | **Yes** | `backend/app/api/v1/destination_routes.py`, `manifests/discourse.yaml` (`instance_param: base_url`) | `test_hard_case_1_retry_after_timeout_no_duplicates` | Adding a 41st Discourse forum or new Lemmy instance requires only `POST /api/v1/destinations` + connection config. |
| **4** | Rules checked before every post (frequency cap, self-promo, link policy, AI disclosure) | **Yes** | `backend/app/rules/engine.py`, `backend/app/publishing/orchestrator.py` | `test_hard_case_5`, `test_hard_case_6`, `test_hard_case_7`, `test_hard_case_12` | `RulesEngine.evaluate()` runs before every publish attempt and persists `rule_decision` (`PASS`, `BLOCKED`, `RESCHEDULED`) and `rule_reasons`. |
| **5** | Never spam, never cheat (Test posts only to local/sandbox, deleted within 10 min, 429 backoff) | **Yes** | `backend/app/certification/engine.py`, `evidence/certification_pack.json` | `test_six_core_connectors_certification`, `test_hard_case_2_platform_rate_limit_429` | Certification deletes test posts immediately and verifies deletion (`cleanup_status: "deleted"`). 429 responses include `retry_after_seconds`. |
| **6** | Safe retries (Same `Idempotency-Key` never creates a second post) | **Yes** | `backend/app/api/v1/publication_routes.py`, `backend/app/models/entities.py` (`IdempotencyRecord`) | `test_hard_case_1_retry_after_timeout_no_duplicates` | Identical key + payload returns existing job (`HTTP 202`); conflicting payload returns `HTTP 409 IDEMPOTENCY_CONFLICT`; orchestrator skips already-live posts. |
| **7** | Secrets protected and simulation mode | **Yes** | `backend/app/core/logging.py` (`redact_secrets`), `.env.example` | `test_secret_redaction_in_logs` | Regex scrubber redacts `Bearer` tokens and `api_key`/`secret` values in JSON logs; simulation mode runs 100% without external keys. |
| **8** | Local test instances (`docker compose up` starts service + Lemmy + Ghost + mocks) | **Yes** | `docker-compose.yml`, `mock-platforms/mock_server.py` | `backend/tests/test_integration_standard.py` | Compose file defines `api`, `worker`, `scheduler`, `postgres`, `redis`, `minio`, `ghost`, `lemmy`, and `mock-platforms`. |
| **9** | Integration Standard followed | **Yes** | `openapi.yaml`, `scripts/batch_runner.py`, `evidence/batch_outputs/batch_summary.json` | `backend/tests/test_integration_standard.py` | All 10 Integration Standard points implemented and verified. |

---

## Tab 2: Levels Reached (Core + Advanced + Outstanding = 40 / 40 Marks)

| Level | Requirement | Status | Evidence File / Endpoint | Test Reference |
| :--- | :--- | :---: | :--- | :--- |
| **Core** | All must-haves pass | **Yes** | See Tab 1 | All 32 tests in `backend/tests/` |
| **Core** | Each Core connector passes full certification run with stored evidence | **Yes** | `evidence/certification_pack.json` | `test_six_core_connectors_certification` |
| **Core** | Errors from each platform mapped to shared error codes (401, 429, 422, disabled) | **Yes** | `backend/app/core/errors.py`, `manifests/*.yaml` | `test_hard_case_2`, `test_hard_case_3`, `test_connector_kill_switch` |
| **Advanced** | Catalogue CSV import: validated, deduplicated, SSRF-checked, 1,000 rows in < 5 min (actual: **0.301s**) | **Yes** | `backend/app/services/catalogue.py`, `evidence/metrics_report.json` | `test_hard_case_9`, `test_1000_row_catalogue_import_performance_and_precision_at_10` |
| **Advanced** | Rules capture: AI step reads community rules text and proposes rules (`human_confirmed: false`) | **Yes** | `POST /api/v1/destinations/ai-propose-rules` (`destination_routes.py`) | Verified via API & OpenAPI spec |
| **Advanced** | Relevance score 1 to 5 against IncuBrix's audience with explanation | **Yes** | `backend/app/recommendations/recommender.py`, `fixtures/destinations_150.csv` | `test_1000_row_catalogue_import_performance_and_precision_at_10` |
| **Advanced** | Tailoring: discussion-first for Discourse, canonical URLs, word-boundary truncation, tags | **Yes** | `backend/app/tailoring/adapter.py` | `test_end_to_end_publishing_job_and_manifest` |
| **Advanced** | Three more connectors: `hashnode`, `slack`, `newsletter` | **Yes** | `backend/app/connectors/{hashnode,slack,newsletter}/`, `manifests/*.yaml` | `test_connector_contract_lifecycle[hashnode/slack/newsletter]` |
| **Outstanding** | Recommender ranks destinations by fit and measures Precision@10 on labelled set (**1.00**) | **Yes** | `fixtures/labelled_recommendations.json`, `evidence/metrics_report.json` | `test_1000_row_catalogue_import_performance_and_precision_at_10` |
| **Outstanding** | `fetch_metrics` works on >= 3 connectors (implemented on 4: `discourse`, `devto`, `hashnode`, `newsletter`) | **Yes** | `POST /connector/v1/{key}/fetch_metrics` | `test_connector_fetch_metrics` |
| **Outstanding** | Recertification scheduler re-tests before 30 days; demotes failing destination with `Alert` | **Yes** | `backend/app/certification/engine.py` (`run_scheduled_recertification`) | `test_hard_case_8_platform_api_schema_change_demotes_certification` |
| **Outstanding** | Real catalogue: >= 150 real, relevant destinations researched (**165 destinations**) | **Yes** | `fixtures/destinations_150.csv` | `test_1000_row_catalogue_import_performance_and_precision_at_10` |

---

## Tab 3: Integration Standard (20 / 20 Marks)

| # | Requirement | Status | Evidence File / Endpoint |
| :- | :--- | :---: | :--- |
| **1** | One-command start (`docker compose up`) and test (`pytest`), `.env.example` | **Yes** | `docker-compose.yml`, `.env.example`, `Makefile` |
| **2** | Documented HTTP API (`openapi.yaml` OpenAPI 3.1.0 matching service, routes under `/api/v1/`) | **Yes** | `openapi.yaml`, `scripts/generate_openapi.py` |
| **3** | Background jobs (`POST` returns 202 with `job_id`, `GET /api/v1/jobs/{id}`, HMAC `X-IncuBrix-Signature`) | **Yes** | `backend/app/api/v1/publication_routes.py`, `backend/app/api/v1/job_routes.py`, `backend/app/publishing/orchestrator.py` |
| **4** | Safe retries (`Idempotency-Key` header on POST) | **Yes** | `backend/app/api/v1/publication_routes.py` (`test_hard_case_1`) |
| **5** | Clear errors (`{"error": {"code", "message", "retryable", "details"}}`) | **Yes** | `backend/app/core/errors.py`, `README.md` |
| **6** | Configuration (Environment variables via Pydantic Settings, zero hardcoded keys) | **Yes** | `backend/app/core/config.py`, `.env.example` |
| **7** | Files in, files out (Upload & download links via MinIO / local S3 fallback) | **Yes** | `backend/app/storage/s3.py`, `backend/app/api/v1/storage_routes.py` |
| **8** | Logs and health (Structured JSON logs with `timestamp`, `level`, `job_id`, `correlation_id`; `/health`, `/ready`) | **Yes** | `backend/app/core/logging.py`, `backend/app/main.py` (`test_health_and_ready_endpoints`) |
| **9** | Output manifest (Providers, versions, timing, cost estimate, warnings, licence/rights) | **Yes** | `backend/app/publishing/orchestrator.py` (`test_end_to_end_publishing_job_and_manifest`) |
| **10** | Batch runner (`python -m scripts.batch_runner --input ... --output ...`) | **Yes** | `scripts/batch_runner.py`, `evidence/batch_outputs/batch_summary.json` |

---

## Tab 4: Hard Cases Tested (All 12 Verified)

| Hard Case Scenario | Status | Automated Test Function (`backend/tests/test_hard_cases.py`) | System Behaviour Verified |
| :--- | :---: | :--- | :--- |
| **1. Publish timeout & retry with same Idempotency-Key** | **Yes** | `test_hard_case_1_retry_after_timeout_no_duplicates` | Returns identical `job_id` (`HTTP 202`), creates 0 duplicate posts; conflicting payload returns `HTTP 409 IDEMPOTENCY_CONFLICT`. |
| **2. HTTP 429 response with reset time** | **Yes** | `test_hard_case_2_platform_rate_limit_429` | Maps to `PLATFORM_RATE_LIMIT`, `retryable: true`, `details.retry_after_seconds: 30`. |
| **3. Expired API token (HTTP 401)** | **Yes** | `test_hard_case_3_expired_token_401` | Maps to `CONNECTION_AUTH_EXPIRED`, `retryable: false`, marks connection `auth_expired: true`. |
| **4. Title or body longer than destination allows** | **Yes** | `test_hard_case_4_content_exceeds_format_limits` | Rejects with `DEST_SPEC_VIOLATION` and exact character-limit violation message. |
| **5. Unsupported media format** | **Yes** | `test_hard_case_5_unsupported_media_rejected` | `RulesEngine` blocks `.exe` upload against `["image/png", "image/jpeg"]` before connector call. |
| **6. Second post inside frequency cap** | **Yes** | `test_hard_case_6_frequency_cap_violation` | `RulesEngine` returns `RESCHEDULED` (`DEST_RULE_FREQUENCY_CAP`) with exact `earliest_eligible_time`. |
| **7. Promotional post to no-promotion community** | **Yes** | `test_hard_case_7_prohibited_self_promotion` | `RulesEngine` deterministically blocks post (`decision: "BLOCKED"`). |
| **8. Platform renames a field in its API response** | **Yes** | `test_hard_case_8_platform_api_schema_change_demotes_certification` | Certification fails, destination is automatically demoted from `L3` to `L0`, disabled, and an `Alert` is created. |
| **9. Invalid CSV (duplicates, bad URLs, invalid lang, SSRF)** | **Yes** | `test_hard_case_9_invalid_catalogue_csv_and_ssrf` | Imports valid row, skips normalized URL duplicate, blocks `klingon_xyz`, missing fields, and `169.254.169.254` SSRF with row-level report. |
| **10. Partner revokes webhook permission** | **Yes** | `test_hard_case_10_partner_webhook_permission_revoked` | Halts publishing immediately with `HTTP 403 CONNECTION_AUTH_EXPIRED`. |
| **11. Non-English community handling** | **Yes** | `test_hard_case_11_non_english_community_eligibility` | Flags `en` content as ineligible for `de` community; marks `de` content as eligible. |
| **12. Destination requiring mandatory AI disclosure** | **Yes** | `test_hard_case_12_mandatory_ai_disclosure` | Blocks undisclosed AI content when strict, or appends required disclosure phrase when authorised. |
