from fastapi import FastAPI

from app.routers import cases, health

app = FastAPI(title="NoticeDesk")
app.include_router(health.router)
app.include_router(cases.router)
