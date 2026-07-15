.PHONY: dev test lint webapp corpus eval deploy

dev:
	uvicorn app.main:app --reload --port $${PORT:-8080}

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

webapp:
	cd webapp && npm run dev

corpus:
	@echo "corpus ingestion pipeline not implemented yet -- arrives in Phase 1 (see docs/SPEC.md #8)."

eval:
	@echo "golden-notice eval + citation verifier not implemented yet -- arrives in Phase 2 (see docs/SPEC.md #14)."

deploy:
	@if [ -z "$$GCP_PROJECT_ID" ]; then \
		echo "GCP_PROJECT_ID is not set -- provision a GCP project first (see docs/SPEC.md #13)."; \
		exit 1; \
	fi
	gcloud run deploy noticedesk \
		--source . \
		--project $$GCP_PROJECT_ID \
		--region asia-south1 \
		--platform managed
