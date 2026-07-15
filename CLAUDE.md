# NoticeDesk
**GST litigation workspace for Indian CA firms — build spec for Claude Code**
**Version 1.0 · July 15, 2026 · Owner: Aman Kumar Maurya**

Workflow: Claude Code starts each phase in **plan mode**, reads the relevant SPEC sections, gets approval, executes. Ambiguity → ask Aman, never invent product behavior. Decision points marked `[DECISION-n]` are Aman's to confirm; do not resolve them silently.

## Project

NoticeDesk: a litigation workspace for small/mid Indian CA firms handling GST notices. Core loop: upload/receive a GST notice → instant AI summary card + deadline captured → guided evidence questionnaire → citation-locked draft reply → CA reviews/edits → export on letterhead → deadline tracked to closure. The firm-level board (all clients, all notices, all deadlines) is the retention product; drafting is a feature inside it. Positioning: NOT a ₹199 pay-per-draft tool — a workspace with a verifiable-citation trust layer. Full spec: `docs/SPEC.md`. Progress log: `PROGRESS.md`.

## Non-negotiable constraints

- Built for Build with Gemini XPRIZE (submit Aug 15, 2026; deadline Aug 17, 1:00 pm PT). Every LLM call in the deployed app uses the **Gemini API**. Deployed on **Cloud Run** with **Firestore**.
- **Citation lock (product-critical):** drafts may cite ONLY items present in our legal corpus, referenced by corpus ID. The renderer inserts the exact stored citation text. If no corpus authority supports a point → insert placeholder `[CA to insert authority]`. A draft with a model-invented citation is a P0 bug, not a quality issue.
- **Every agent action logged** to `agent_runs` (hackathon evidence + audit trail for professional users).
- Repo shared with judges (testing@devpost.com, judging@hacker.fund): zero secrets in code or git history; `.env.example` only; rotate anything that leaks.
- All code newly written after May 19, 2026; no imports from Aman's prior projects.
- **PII discipline:** GSTINs, client names, financials are sensitive. No client data in stdout logs; bodies live in Firestore only. Never send client documents to any non-Gemini third-party API. State "your data is never used to train models" only if config keeps it true (Gemini API with training off).
- **No GST-portal credentials, ever, in MVP.** We do not ask for, store, or automate with a CA's GSTN login. Auto-fetch is a post-hackathon GSP-partnership feature.

## Stack (locked — do not substitute)

- Python 3.11, FastAPI, Uvicorn; `google-genai` SDK (models via env `GEMINI_MODEL_FAST` / `GEMINI_MODEL_SMART` / `GEMINI_MODEL_EMBED` — verify current IDs at ai.google.dev; never hardcode)
- Firestore (Native mode) + Firestore vector search for corpus retrieval
- Document AI (OCR for scanned/photographed notices); Cloud Storage for originals + exports
- Frontend: Vite + React + Tailwind in `/webapp`, served as static build by FastAPI
- WhatsApp Business Cloud API for intake + deadline reminders (companion channel, not primary UI)
- Razorpay (payment links first; webhook for reconciliation)
- Cloud Scheduler → OIDC-protected task endpoints; Secret Manager for credentials
- Tests: pytest. Deploy: Dockerfile → Cloud Run, region `asia-south1`
- Exports: `python-docx` for Word, WeasyPrint or equivalent for PDF (ask before adding alternatives)

## Commands

```bash
make dev         # FastAPI local with reload
make test        # pytest -q
make lint        # ruff check . && ruff format --check .
make webapp      # cd webapp && npm run dev
make corpus      # run corpus ingestion pipeline (scripts/corpus_ingest.py)
make eval        # run golden-notice eval + citation verifier (must pass before deploy)
make deploy      # gcloud run deploy (Makefile)
```

## Working agreement

- Plan mode per phase; approval before code. Small imperative commits.
- `make eval` is a deploy gate: extraction accuracy on golden notices + zero citation-verifier failures.
- Tests required for: citation verifier, deadline computation, OCR fallback routing, webhook signatures, JSON-parse fallbacks, access control (firm isolation).
- Files under ~400 lines; split modules. Ask before new dependencies.
- Prompts in `app/prompts/*.py` as versioned constants; never inline.
- Update `PROGRESS.md` each session (shipped / blocked / next).
