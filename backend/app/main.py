from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    auth,
    clients,
    classification,
    cma_reports,
    conversion,
    documents,
    extraction,
    rollover,
    tasks,
    users,
)

settings = get_settings()

app = FastAPI(
    title="CMA Automation API",
    version="1.0.0",
    description="Automates CMA document preparation for CA firms",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(documents.router)
app.include_router(extraction.router)
app.include_router(tasks.router)
app.include_router(classification.router)
app.include_router(cma_reports.router)
app.include_router(conversion.router)
app.include_router(rollover.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
