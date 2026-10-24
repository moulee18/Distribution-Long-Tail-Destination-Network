import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import async_engine, Base
from backend.app.core.errors import IncuBrixException, ErrorCode
from backend.app.core.logging import logger, correlation_id_ctx
from backend.app.connectors.registry import registry

from backend.app.api.connector_routes import router as connector_router
from backend.app.api.v1.content_routes import router as content_router
from backend.app.api.v1.destination_routes import router as destination_router
from backend.app.api.v1.catalogue_routes import router as catalogue_router
from backend.app.api.v1.recommendation_routes import router as recommendation_router
from backend.app.api.v1.publication_routes import router as publication_router
from backend.app.api.v1.job_routes import router as job_router
from backend.app.api.v1.certification_routes import router as certification_router
from backend.app.api.v1.connector_admin_routes import router as connector_admin_router
from backend.app.api.v1.analytics_routes import router as analytics_router
from backend.app.api.v1.storage_routes import router as storage_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting IncuBrix Distribution Hub backend...")
    manifests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "manifests"))
    registry.load_manifests(manifests_dir)
    
    # Create tables if not existing
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {str(e)}")
        
    yield
    # Shutdown
    logger.info("Shutting down IncuBrix Distribution Hub backend...")

app = FastAPI(
    title="IncuBrix Distribution Hub",
    description="Intelligent Long-Tail Content Distribution Network",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID Middleware (Integration Standard Point 8)
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    correlation_id_ctx.set(corr_id)
    response: Response = await call_next(request)
    response.headers["X-Correlation-Id"] = corr_id
    return response

# Custom Exception Handlers (Integration Standard Point 5)
@app.exception_handler(IncuBrixException)
async def incubrix_exception_handler(request: Request, exc: IncuBrixException):
    logger.warning(f"[{exc.code.value}] {exc.message} (details={exc.details})")
    return exc.to_response()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": f"Internal server error: {str(exc)}",
                "retryable": False,
                "details": {},
            }
        },
    )

# Health & Ready Endpoints (Integration Standard Point 8)
@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "incubrix-distribution-hub",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "simulation_mode": settings.SIMULATION_MODE,
    }

@app.get("/ready", tags=["System Health"])
async def readiness_check():
    checks = {"database": False, "connectors": False}
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    conns = registry.list_connectors()
    checks["connectors"] = len(conns) > 0
    checks["loaded_connectors_count"] = len(conns)

    is_ready = checks["database"] and checks["connectors"]
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        },
    )

# Connector Contract Routes (Appendix A: POST /connector/v1/{connector_key}/{method})
app.include_router(connector_router)

# Application Routes (Integration Standard: /api/v1/...)
app.include_router(content_router, prefix="/api/v1")
app.include_router(destination_router, prefix="/api/v1")
app.include_router(catalogue_router, prefix="/api/v1")
app.include_router(recommendation_router, prefix="/api/v1")
app.include_router(publication_router, prefix="/api/v1")
app.include_router(job_router, prefix="/api/v1")
app.include_router(certification_router, prefix="/api/v1")
app.include_router(connector_admin_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(storage_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/ui/index.html")

# Serve Frontend Static Files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="frontend")
