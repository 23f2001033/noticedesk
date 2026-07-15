# NoticeDesk

GST litigation workspace for Indian CA firms — built for the Build with Gemini XPRIZE.

Upload or forward a GST notice → instant AI summary card with deadline tracking → guided
evidence questionnaire → citation-locked draft reply → CA reviews and exports on letterhead →
deadline tracked through to closure.

Full specification: [`docs/SPEC.md`](docs/SPEC.md). Session working agreement and constraints:
[`CLAUDE.md`](CLAUDE.md). Build progress log: [`PROGRESS.md`](PROGRESS.md).

**Status:** Phase 0 (scaffold). Not yet deployed.

## Local development

```bash
cp .env.example .env   # fill in values as they become available
make dev                # FastAPI local with reload
make test                # pytest -q
make lint                 # ruff check + format check
```

See `CLAUDE.md` for the full command list and the phased build plan in `docs/SPEC.md` §15.
