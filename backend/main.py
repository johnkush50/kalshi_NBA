"""
Kalshi NBA Paper Trading Application - FastAPI Main Application.

Entry point for the backend API server.
Configures FastAPI with routes, middleware, and startup/shutdown events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.config.settings import settings
from backend.utils.logger import setup_logging
from backend.api.routes import health, games, strategies, trading, aggregator

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


# ============================================================================
# FastAPI Application Initialization
# ============================================================================

app = FastAPI(
    title="Kalshi NBA Paper Trading API",
    description="Real-time paper trading of NBA prediction markets on Kalshi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# CORS Middleware Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Include Routers
# ============================================================================

# Health check endpoint
app.include_router(
    health.router,
    prefix="/api",
    tags=["Health"]
)

# Game management endpoints
app.include_router(
    games.router,
    prefix="/api/games",
    tags=["Games"]
)

# Strategy management endpoints
app.include_router(
    strategies.router,
    prefix="/api/strategies",
    tags=["Strategies"]
)

# Trading endpoints
app.include_router(
    trading.router,
    prefix="/api/trading",
    tags=["Trading"]
)

# Aggregator endpoints
app.include_router(
    aggregator.router,
    prefix="/api/aggregator",
    tags=["Aggregator"]
)


# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Execute on application startup.

    Initializes connections, logging, and background tasks.
    """
    logger.info("=" * 60)
    logger.info("Kalshi NBA Paper Trading Application Starting")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Backend URL: {settings.backend_url}")
    logger.info(f"Frontend URL: {settings.frontend_url}")
    logger.info(f"Log Level: {settings.log_level}")

    # Test database connection
    try:
        from backend.config.supabase import check_connection
        connection_ok = await check_connection()
        if connection_ok:
            logger.info("✓ Supabase connection successful")
        else:
            logger.warning("⚠ Supabase connection failed - check credentials")
    except Exception as e:
        logger.error(f"✗ Error checking Supabase connection: {e}", exc_info=True)

    # Start data aggregator
    try:
        from backend.engine.aggregator import get_aggregator
        agg = get_aggregator()
        await agg.start()
        logger.info("✓ Data aggregator started")
    except Exception as e:
        logger.error(f"✗ Failed to start data aggregator: {e}")

    logger.info("Application startup complete")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute on application shutdown.

    Cleans up connections and background tasks.
    """
    logger.info("=" * 60)
    logger.info("Shutting down Kalshi NBA Paper Trading Application")
    logger.info("=" * 60)

    # Stop data aggregator
    try:
        from backend.engine.aggregator import get_aggregator
        agg = get_aggregator()
        await agg.stop()
        logger.info("✓ Data aggregator stopped")
    except Exception as e:
        logger.error(f"✗ Error stopping data aggregator: {e}")

    logger.info("Cleanup complete")
    logger.info("Application shutdown complete")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint providing API information.

    Returns:
        dict: API information and available endpoints.
    """
    return {
        "name": "Kalshi NBA Paper Trading API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "docs": f"{settings.backend_url}/docs",
        "health": f"{settings.backend_url}/api/health",
    }


# ============================================================================
# Run Application (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable hot reload in development
        log_level=settings.log_level.lower()
    )
