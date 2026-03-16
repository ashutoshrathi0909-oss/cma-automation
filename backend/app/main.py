import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import get_service_client
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

logger = logging.getLogger(__name__)

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


# ── Exception handlers ────────────────────────────────────────────────────────


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic RequestValidationError into a structured 422 response."""
    fields = []
    for error in exc.errors():
        loc = error.get("loc", ())
        # Strip only the leading "body" segment (FastAPI prepends it for request-body fields)
        trimmed = loc[1:] if loc and loc[0] == "body" else loc
        field_name = ".".join(str(p) for p in trimmed) if trimmed else (str(loc[0]) if loc else "")
        fields.append({"field": field_name, "message": error.get("msg", "")})

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation failed",
            "code": "VALIDATION_ERROR",
            "fields": fields,
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions — logs server-side, never leaks details."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> dict:
    """Health check. Probes DB connectivity and returns degraded status on failure."""
    db_status = "ok"
    try:
        svc = get_service_client()
        svc.table("user_profiles").select("id").limit(1).execute()
    except Exception as exc:
        logger.warning("Health check: DB probe failed — %s", exc)
        db_status = "error"

    return {"status": "ok" if db_status == "ok" else "degraded", "db": db_status}
