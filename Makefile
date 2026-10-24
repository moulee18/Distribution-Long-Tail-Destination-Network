.PHONY: up down test batch evidence openapi dev

# Start complete environment with Docker Compose (Integration Standard 1)
up:
	docker compose up --build -d

down:
	docker compose down

# Run complete automated test suite (Unit, Contract, Hard Cases, Integration Standard, E2E)
test:
	pytest backend/tests -v

# Run Integration Standard CLI Batch Runner
batch:
	python -m scripts.batch_runner --input fixtures/batch_inputs --output evidence/batch_outputs

# Generate Certification Pack and Metrics Report
evidence:
	python scripts/generate_evidence_and_metrics.py

# Regenerate OpenAPI 3.1.0 YAML specification
openapi:
	python scripts/generate_openapi.py

# Run local development server (standalone mode)
dev:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
