# Sources & Third-Party Disclosures (`SOURCES.md`)

In accordance with the IncuBrix Assessment Tools & Resources rules, every library, API, model, dataset, and container image used in this project is disclosed below along with its licence. **All components are commercially usable (MIT, BSD, Apache-2.0, PostgreSQL); zero AGPL or non-commercial (CC BY-NC) assets are included in the shipped service.**

---

## 1. Python Backend Libraries

| Package | Version | Licence | Purpose |
| :--- | :--- | :--- | :--- |
| `fastapi` | `>=0.110.0` | MIT | HTTP API framework for `/api/v1/` and `/connector/v1/` |
| `uvicorn` | `>=0.28.0` | BSD-3-Clause | ASGI server |
| `pydantic` & `pydantic-settings` | `>=2.6.0` | MIT | Data validation, schemas, and environment settings |
| `sqlalchemy` | `>=2.0.28` | MIT | Async/sync ORM and relational persistence |
| `alembic` | `>=1.13.1` | MIT | Database schema migrations |
| `asyncpg` | `>=0.29.0` | Apache-2.0 | Async PostgreSQL driver |
| `psycopg2-binary` | `>=2.9.9` | LGPL-3.0 (with linking exception) | Sync PostgreSQL driver for migrations/workers |
| `aiosqlite` | `>=0.20.0` | MIT | Async SQLite driver for standalone & test execution |
| `greenlet` | `>=3.0.3` | MIT | Concurrency primitive for SQLAlchemy asyncio |
| `redis` | `>=5.0.3` | MIT | Redis client for broker and caching |
| `celery` | `>=5.3.6` | BSD-3-Clause | Distributed background job queue and beat scheduler |
| `httpx` | `>=0.27.0` | BSD-3-Clause | Async HTTP client for external connectors and ASGI testing |
| `pyyaml` | `>=6.0.1` | MIT | Connector manifest YAML parser and OpenAPI generator |
| `python-multipart` | `>=0.0.9` | Apache-2.0 | Multipart form and CSV file upload parsing |
| `cryptography` | `>=42.0.5` | Apache-2.0 / BSD | Cryptographic primitives |
| `minio` | `>=7.2.5` | Apache-2.0 | S3-compatible object storage client (Apache-2.0 SDK) |
| `pytest` & `pytest-asyncio` | `>=8.1.1` | MIT / Apache-2.0 | Automated unit, contract, hard-case, and E2E testing |

---

## 2. Platform APIs & Protocols Targeted by Connectors

1. **Discourse REST API**: Topic creation (`POST /posts.json`), status (`GET /posts/{id}.json`), deletion (`DELETE /posts/{id}.json`).
2. **Lemmy HTTP API v3**: Post creation (`POST /api/v3/post`), status (`GET /api/v3/post`), deletion (`POST /api/v3/post/delete`).
3. **Dev.to / Forem API v1**: Article creation (`POST /api/articles`), status (`GET /api/articles/{id}`), unpublish adapter (`PUT /api/articles/{id}`).
4. **Ghost Admin API v5**: Post creation (`POST /ghost/api/admin/posts/`), status, and deletion (`DELETE /ghost/api/admin/posts/{id}/`).
5. **IncuBrix Partner Signed Webhook Protocol**: HMAC-SHA256 (`X-IncuBrix-Signature` + `X-IncuBrix-Timestamp`) over HTTP JSON.
6. **Hashnode GraphQL/REST API, Slack Web API, Newsletter Campaign API**: Modelled via manifest-driven adapters.

---

## 3. AI Models & Providers

* **Default Provider (`MockAIProvider` in `backend/app/tailoring/adapter.py`)**: Deterministic, rule-aware content tailoring and community rules parser written in-house. Zero external API calls or costs; 100% commercially owned.
* **Configurable External LLM Adapter**: Swappable via `AI_PROVIDER` and `AI_API_KEY` environment variables.

---

## 4. Datasets & Media Assets

* **Destination Catalogue (`fixtures/destinations_150.csv`)**: 165 researched real-world community metadata records (public URLs, community categories, and public posting guidelines) curated specifically for IncuBrix's target audience (AI, video, marketing, SaaS, creators, founders).
* **Labelled Recommendation Evaluation Set (`fixtures/labelled_recommendations.json`)**: Original ground-truth benchmark queries created for Precision@10 verification.
* **Media Assets**: No third-party copyrighted images, voices, faces, or non-commercial media are used anywhere in the repository.
