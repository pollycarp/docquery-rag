"""
FastAPI Application Entry Point
--------------------------------
This is the file that starts the whole web server.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import init_db
from app.logging_config import setup_logging, logger
from app.middleware import RequestLoggingMiddleware
from app.api.routes import ingest, query, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup (before yield) and shutdown (after yield)."""
    setup_logging()
    logger.info("startup", extra={"event": "server_starting"})
    init_db()
    logger.info("startup", extra={"event": "database_ready"})
    yield
    logger.info("shutdown", extra={"event": "server_stopping"})


# ── Rate Limiter ──────────────────────────────────────────────────────────────
# Limits requests per IP address. Limits are applied per-route (see routes/).
# Key function: get_remote_address identifies clients by their IP.
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Document Q&A RAG API",
    description="Ingest documents and ask questions with cited answers.",
    version="0.5.0",
    lifespan=lifespan,
)

# Attach limiter to app state so route decorators can access it
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware — runs on every request
app.add_middleware(RequestLoggingMiddleware)

# Routes
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(stats.router)


# ── Prometheus Metrics ────────────────────────────────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
except ImportError:
    pass  # optional — install with: pip install prometheus-fastapi-instrumentator


# ── Global Error Handlers ─────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": " → ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_error", extra={"error": str(exc)})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected server error occurred. Please try again."},
    )


# ── Public Endpoints ──────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health_check():
    """Public endpoint — no API key needed. Confirms the server is running."""
    return {"status": "ok"}
