"""MedBuddy FastAPI application."""

from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api import chat, documents, episodes, medications, profiles
from backend.config import settings
from backend.database import _json_default
from backend.schemas import HealthResponse


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route registration ---
app.include_router(profiles.router)
app.include_router(episodes.router)
app.include_router(medications.router)
app.include_router(documents.router)
app.include_router(chat.router)


def _make_json_serializable(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable values (e.g. ValueError) to strings."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Exception):
        return str(obj)
    if isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    return str(obj)


# --- Consistent error responses per API contract ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert FastAPI validation errors to the documented error envelope."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "ERR_VALIDATION",
                "message": "Validation error",
                "details": _make_json_serializable(exc.errors()),
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Convert HTTPExceptions to the documented error envelope."""
    # If detail is already a structured error dict (raised by our endpoints),
    # preserve it as-is instead of rewrapping.
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    code_map = {
        404: "ERR_NOT_FOUND",
        409: "ERR_CONFLICT",
        413: "ERR_PAYLOAD_TOO_LARGE",
        415: "ERR_UNSUPPORTED_FILE",
        422: "ERR_VALIDATION",
        500: "ERR_INTERNAL",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code_map.get(exc.status_code, "ERR_ERROR"),
                "message": str(exc.detail),
                "details": None,
            }
        },
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Simple health check endpoint."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        env=settings.app_env,
    )
