import pathlib

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routers import cases, health
from app.services.webapp_static import resolve_webapp_file

app = FastAPI(title="NoticeDesk")
app.include_router(health.router)
app.include_router(cases.router)

WEBAPP_DIST = (pathlib.Path(__file__).resolve().parent.parent / "webapp" / "dist").resolve()

if WEBAPP_DIST.is_dir():

    @app.get("/{full_path:path}")
    def serve_webapp(full_path: str) -> FileResponse:
        """Serves the built React SPA for any route the API doesn't otherwise
        handle. Only registered once `webapp/dist` exists (after `npm run
        build`) -- local Python-only dev without a webapp build is unaffected."""
        return FileResponse(resolve_webapp_file(full_path, WEBAPP_DIST))
