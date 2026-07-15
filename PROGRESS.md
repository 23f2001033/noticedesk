# Progress log

## 2026-07-16 — Phase 0: Scaffold

**Shipped:**
- Repo scaffold: `pyproject.toml`, `Makefile`, `Dockerfile`, `.env.example`, `.gitignore`/`.dockerignore`, `README.md`, `LICENSE` (placeholder).
- FastAPI app (`app/main.py`) with `GET /healthz`.
- Auth skeleton: `app/services/auth.py` (Firebase ID token verification) + `app/deps.py` (`get_current_user`, `get_current_firm` firm-scoping dependency), unit-tested with mocked tokens/Firestore.
- Firestore wiring: `app/services/firestore.py` lazy client construction (no live calls yet).
- CI (`.github/workflows/ci.yml`): lint, test, Docker build (Cloud Run-readiness check), gitleaks secret scan.
- Tests: `tests/test_health.py`, `tests/test_auth.py`.

**Blocked:**
- No GCP/Firebase project provisioned yet — `make deploy` is written but not runnable; real Firestore/Firebase Auth wiring is still against no live project.
- `LICENSE` content undecided (proprietary vs open-source).

**Next (Phase 1):**
- Provision GCP + Firebase project; run first real `make deploy`.
- `webapp/` scaffold (Vite + React + Tailwind) with a real Login page.
- Intake (web upload), OCR routing, classifier + extractor agents, summary card, deadline board, WhatsApp reminders, corpus pipeline + first ~40 corpus items.

## 2026-07-16 — Phase 1, slice 1: data model + deadline math + classifier/extractor agents

**Shipped:**
- Full §3 data model as Pydantic models in `app/models/` (Firm, User, Client, Case, CaseDocument, Extraction, DiscrepancyRow, Draft, CorpusItem, CorpusChunk, AgentRun, Payment, MetricsDaily, KBGap).
- Deadline computation (`app/services/deadlines.py`): statutory-default due dates, T-7/T-3/T-1 reminder scheduling, 21:00–09:00 IST quiet-hours handling, overdue check. **ASMT-10's 30-day default is reasonably confident (Rule 99(1) r/w Section 61); DRC-01A (15d) and DRC-01 (30d) are placeholders — need Aman/CA-advisor sign-off before real due dates ship.** By construction, any case using a computed default carries `due_date_source="statutory_default"` and `due_date_confirmed=False` so the CA is always prompted, regardless of whether the day-count itself is later corrected.
- `agent_runs` logging (`app/services/logging_runs.py`), PII-minimized input digest truncation.
- Gemini wrapper (`app/services/gemini.py`): JSON-schema calls + parse-fallback handling. **Not yet smoke-tested against a live API key** — written from current understanding of the `google-genai` SDK surface, needs a real run once `GEMINI_API_KEY` exists.
- Classifier + extractor agents (`app/agents/`) with versioned prompts (`app/prompts/`), both falling back safely (not raising) on a Gemini JSON-parse failure and logging `status=fallback`.
- Tests for all of the above (28 passing) — Gemini and Firestore calls mocked throughout since no live credentials exist yet.

**Blocked (same root cause — no GCP project, Aman fixing Google Cloud Console access):**
- Can't smoke-test `app/services/gemini.py` or `app/services/firestore.py` against anything real.
- `make deploy` still unrun.

**Also open:**
- DRC-01A / DRC-01 statutory default day-counts in `app/services/deadlines.py` need legal verification (flagged in code).

**Next:**
- Intake router (`POST /api/cases`) + OCR routing (native text vs Document AI fallback).
- Summary card assembly wiring classifier → extractor → Case/Extraction write → deadline board.
- `webapp/` scaffold with Login + Board pages.
- Corpus pipeline tooling (`scripts/corpus_ingest.py`, `corpus_src/` schema) — actual corpus content is Aman's curation task, not something to fabricate.
- WhatsApp reminders — needs WhatsApp Business Cloud API credentials.
- Golden-notice eval harness — needs real anonymized notices from Aman's CA network.

## 2026-07-16 — Phase 1, slice 2: intake pipeline (upload → OCR → classify → extract → persist)

**Shipped:**
- Cloud Storage upload (`app/services/storage.py`) — lazy client, `gs://` ref, raises clearly if `CLOUD_STORAGE_BUCKET` isn't configured.
- Document AI OCR wrapper (`app/services/document_ai.py`). **Not yet smoke-tested against a live processor** — same caveat as `gemini.py`, needs a real run once a processor is provisioned.
- OCR routing (`app/services/ocr.py`, §5 step 2): native PDF text via `pypdf` first, falls back to Document AI when text density is low (<200 chars/page) or the input is an image. New dependency `pypdf` — confirmed with Aman before adding, per the "ask before new dependencies" rule.
- Case ingestion pipeline (`app/services/case_pipeline.py`): wires upload → OCR → classifier → extractor → due-date resolution (extracted vs statutory-default, always `due_date_confirmed=False`) → writes `cases/{id}`, `cases/{id}/documents/{doc}`, `cases/{id}/extraction/current`.
- `POST /api/cases` router (`app/routers/cases.py`, §12), firm-scoped via existing auth deps.
- Tests for all of the above (42 passing total) — Firestore/Storage/Document AI/Gemini all mocked; app boot + `/healthz` + an unauthenticated `POST /api/cases` (401) smoke-tested against a live local uvicorn process.

**Blocked (same root cause — no GCP project, Aman fixing Google Cloud Console access):**
- `storage.py`, `document_ai.py`, `firestore.py`, `gemini.py` all unverified against anything live.

**Next:**
- Deadline board write + reminder scheduling wiring (Case → reminder queue).
- `webapp/` scaffold with Login + Board pages.
- Corpus pipeline tooling + WhatsApp reminders + golden-notice eval harness (all still blocked on external inputs — see prior entry).
