"""FastAPI application — main entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.routes import router
from app.core.config import get_settings
from app.db.database import get_engine, Base
from app.observability.tracing import setup_tracing
import structlog

logger = structlog.get_logger()
settings = get_settings()


def __getattr__(name: str):
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("starting_application", service=settings.otel_service_name, env=settings.environment)

    # Initialize tracing
    setup_tracing()

    # Create database tables (in production use Alembic migrations)
    eng = get_engine()
    async with eng.begin() as conn:
        # Enable pgvector extension
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")

    yield

    await eng.dispose()
    logger.info("application_shutdown")


app = FastAPI(
    title="RAG Evaluation & Observability Platform",
    description="A general-purpose RAG platform with evaluation, query logging, and observability.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Enforce defensive HTTP security headers on all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
if settings.prometheus_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "RAG Evaluation & Observability Platform", "docs": "/docs"}
