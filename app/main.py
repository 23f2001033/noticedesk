from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="NoticeDesk")
app.include_router(health.router)
