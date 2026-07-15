# NoticeDesk webapp

Vite + React + TypeScript + Tailwind, served as a static build by the FastAPI
app (see `app/main.py` and the root `Dockerfile`). See `../CLAUDE.md` and
`../docs/SPEC.md` §11 for the product spec.

```bash
cp .env.example .env.local   # fill in Firebase web app config once it exists
npm install
npm run dev      # local dev server, proxies nothing -- point VITE_API_BASE_URL
                  # at a running `make dev` backend, or leave blank when the
                  # backend serves this build itself
npm run build     # type-check + production build to dist/
npm run lint      # oxlint
```

**Status:** Login (Google sign-in) + Board pages only, matching what the
backend supports so far. No live Firebase project yet, so sign-in hasn't
been smoke-tested against real credentials (see `../PROGRESS.md`). Email-link
sign-in (also named in the spec) is deferred until Google sign-in is verified
against a real project.
