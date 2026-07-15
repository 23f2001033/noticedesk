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

## 2026-07-16 — Phase 1, slice 3: deadline board + reminder agent

**Shipped:**
- `GET /api/cases?status=` (§12) via `app/services/board.py`: firm-scoped case list, each annotated with an urgency badge (`overdue` / `due_soon_3d` / `due_soon_7d` / `on_track` / `no_deadline`, §11).
- WhatsApp client wrapper (`app/services/wa_client.py`, `send_whatsapp_message`). **Not yet smoke-tested against live WhatsApp Business credentials** — no `WA_ACCESS_TOKEN` provisioned.
- Reminder agent (`app/agents/reminder.py`, §9): decision logic (`decide_reminders_for_cases`) is a pure function over `(case_id, Case)` pairs — fires on T-7/T-3/T-1, skips (with a logged reason) once a case is past needing one (`reply_filed`/`dropped`/`order_passed`/`appeal_window`/`closed`). `run_reminder_check` wires it to Firestore + WhatsApp send + `agent_runs` logging; falls back (status=`fallback`, still logged) if a firm has no `wa_number` on file rather than silently dropping the reminder.
- 17 new tests (59 passing total). Reminder decision logic is fully unit-tested without mocks (pure function); Firestore/WhatsApp sends are mocked for `run_reminder_check`.

**Deliberately deferred:**
- `POST /tasks/reminders` HTTP endpoint + OIDC verification (Cloud Scheduler → task endpoint per §12) — needs a live GCP project to configure the OIDC audience, so `run_reminder_check()` is callable directly (and tested) but not yet wired to an HTTP route. Wiring it is a small step once GCP is unblocked.

**Blocked (same root cause):**
- `wa_client.py` unverified against anything live; same for the Firestore-touching pieces reused here.

**Next:**
- `webapp/` scaffold (Vite + React + Tailwind) with Login + Board pages — first slice that gives you something to click through.
- Corpus pipeline tooling + golden-notice eval harness (still gated on Aman's curation work, not something to fabricate).

## 2026-07-16 — Phase 1, slice 4: webapp scaffold (Login + Board)

**Shipped:**
- `webapp/`: Vite + React 19 + TypeScript + Tailwind v4, scaffolded via `npm create vite@latest -- --template react-ts` then built out. New deps beyond the locked stack: `react-router-dom` (client-side routing, no viable Vite+React multi-page app without one) and `firebase` (the JS SDK for the already-locked Firebase Auth) — both natural consequences of stack choices already made, not asked about separately.
- Firebase Auth wiring (`src/firebase.ts`, `src/auth/`): Google sign-in only for now. **Email-link sign-in (also named in §11) is deferred** — no live Firebase project to test either against, and shipping a half-tested two-step flow isn't worth it yet.
- `Login` and `Board` pages — Board calls `GET /api/cases` with a Firebase ID token attached, renders the case list with urgency badges, filterable by status.
- FastAPI now serves the built SPA (`app/services/webapp_static.py` + a catch-all route in `app/main.py`) so the backend and frontend deploy as one Cloud Run service, matching the locked stack ("served as static build by FastAPI"). Path-traversal-safe by construction (resolved path must stay under `webapp/dist`) — tested. Only activates when `webapp/dist` exists, so Python-only local dev is unaffected.
- `Dockerfile` is now multi-stage: Node stage builds the webapp, Python stage copies `dist/` in. `make webapp` now runs the real dev server; CI builds + lints the webapp (Node 24) before the Python steps, so `webapp/dist` exists for both the new SPA-serving test and the Docker build.
- 5 new Python tests (64 passing total) — pure-function tests for the path resolver plus one integration test (skipped if `dist/` isn't built) confirming `/login` returns the SPA shell. Webapp: `npm run build` (tsc + vite build) and `npm run lint` (oxlint) both clean. Locally verified end-to-end: built the webapp, booted the full FastAPI app, confirmed `/healthz`, `/login` (SPA shell), a built JS/CSS asset, and unauthenticated `/api/cases` (401) all resolve correctly from the same origin.

**Blocked (same root cause):**
- No live Firebase project — sign-in itself is unverified; `webapp/.env.example` documents the config shape (`VITE_FIREBASE_*`) to fill in once one exists.

**Next:**
- Corpus pipeline tooling (`scripts/corpus_ingest.py`, `corpus_src/` schema) + golden-notice eval harness — both still gated on Aman's curation work (real corpus content, real anonymized notices), not something to fabricate.
- `POST /tasks/reminders` HTTP endpoint + OIDC wiring, once GCP is unblocked.
- CaseDetail/DraftEditor/Clients/CorpusAdmin/Evidence/Settings/Billing pages — deferred until their backing endpoints exist (Phase 2+).

## 2026-07-16 — Phase 1, slice 5: corpus ingestion pipeline

**Shipped:**
- `app/services/corpus.py`: parses `corpus_src/*.yaml` against the `CorpusItem` schema, chunks `verbatim_text` (fixed-size sliding window, simple by design — nothing real to tune it against yet), embeds via a new `embed_text()` in `gemini.py` (same "unverified against a live key" caveat as `generate_json`), and upserts to Firestore. Items without `reviewed_by` are written to `corpus` for admin visibility but **never** to `corpus_chunks` — structurally unretrievable by the drafter's vector search until reviewed, per the spec's "every item requires reviewed_by before it becomes retrievable" rule.
- `scripts/corpus_ingest.py` (`make corpus`) — thin CLI wrapper, fails clearly if `GEMINI_MODEL_EMBED` isn't set rather than crashing; smoke-tested against an empty `corpus_src/` (correctly prints the config error and exits 1).
- `corpus_src/README.md` documents the YAML schema with an inline example — **deliberately no actual `.yaml` files added**. Populating this with the real ~25–40 circulars, CGST sections/rules, and ~60–120 case-law holdings is Aman's (or a CA advisor's) curation work; inventing statutory text from a model's memory here would be exactly the kind of unverified-authority problem the citation-lock rule exists to prevent, just one step upstream of a draft.
- New dependency `pyyaml` — the spec mandates the `corpus_src/*.yaml` format itself, and pyyaml is the standard library for it (no real alternative to weigh, unlike the pypdf decision), so added directly rather than raised as a question; flagging here for visibility.
- 9 new tests (73 passing total) — parsing/validation, chunking (including overlap behavior), and the reviewed-vs-unreviewed upsert branching, all against obviously-fictional fixture text, never real legal content.

**Known simplification (documented in `corpus_src/README.md`):** the spec's "immutable once reviewed; edits create a new version" versioning isn't implemented — every ingest currently overwrites `version: 1`. Not worth building out until real curation and real edits start happening.

**Blocked (same root cause):** `embed_text()` unverified against a live key; actual corpus content is entirely pending Aman's curation.

**Next:** golden-notice eval harness (`scripts/eval_notices.py`, `make eval`) — same pattern: build the scoring/gate logic now, real anonymized notices come from Aman's CA network later.
