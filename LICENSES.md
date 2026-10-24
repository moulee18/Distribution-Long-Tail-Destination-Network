# Licence & Commercial Usability Compliance (`LICENSES.md`)

## 1. Repository Code Licence

All original source code, connector manifests, schemas, frontend assets, test suites, and documentation in this repository are authored for the IncuBrix Engineering Assessment and licensed for commercial use under the **MIT Licence** (or per written agreement with IncuBrix Private Limited).

## 2. Third-Party Dependency Licence Audit

We audited all shipped runtime dependencies (`backend/requirements.txt`) to ensure **100% commercial compatibility** and **zero AGPL or non-commercial (CC BY-NC) code in the shipped service**:

| Dependency | Licence | Commercial Use Allowed? | AGPL Free? |
| :--- | :--- | :---: | :---: |
| `fastapi` | MIT | Yes | Yes |
| `uvicorn` | BSD-3-Clause | Yes | Yes |
| `pydantic` / `pydantic-settings` | MIT | Yes | Yes |
| `sqlalchemy` | MIT | Yes | Yes |
| `alembic` | MIT | Yes | Yes |
| `asyncpg` | Apache-2.0 | Yes | Yes |
| `aiosqlite` | MIT | Yes | Yes |
| `greenlet` | MIT | Yes | Yes |
| `redis` | MIT | Yes | Yes |
| `celery` | BSD-3-Clause | Yes | Yes |
| `httpx` | BSD-3-Clause | Yes | Yes |
| `pyyaml` | MIT | Yes | Yes |
| `python-multipart` | Apache-2.0 | Yes | Yes |
| `cryptography` | Apache-2.0 / BSD | Yes | Yes |
| `minio` (Python SDK) | Apache-2.0 | Yes | Yes |
| `aiofiles` | Apache-2.0 | Yes | Yes |
| `python-dateutil` | Apache-2.0 / BSD | Yes | Yes |

*Note on Local Infrastructure Containers*: In `docker-compose.yml`, PostgreSQL (`PostgreSQL Licence`), Redis (`BSD`), and Ghost (`MIT`) are permissive. MinIO server and Lemmy server are used solely as external local development/test infrastructure containers over standard HTTP/S3 network protocols and are never linked into or shipped as part of the IncuBrix connector service code.
