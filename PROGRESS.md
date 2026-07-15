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
