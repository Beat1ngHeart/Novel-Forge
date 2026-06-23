import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.llm.registry import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


async def _check_database() -> tuple[bool, float]:
    """Check database connectivity. Returns (ok, latency_ms)."""
    import time

    try:
        start = time.monotonic()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        return True, round(latency, 1)
    except Exception:
        return False, 0.0


async def _check_llm() -> tuple[bool, dict]:
    """Check LLM provider health. Returns (ok, info)."""
    try:
        provider = get_llm_provider()
        info = await provider.health_check()
        return True, info
    except Exception as e:
        return False, {"error": str(e)}


@router.get("/health")
async def health():
    """Root health check — lightweight status for load balancers."""
    db_ok, db_latency = await _check_database()
    llm_ok, llm_info = await _check_llm()

    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "database": "connected" if db_ok else "disconnected",
        "llm": {"provider": settings.LLM_PROVIDER, "status": "ok" if llm_ok else "error", **llm_info},
    }


@router.get("/api/v1/system/info")
async def system_info():
    """System configuration information."""
    return {
        "app_name": settings.APP_NAME,
        "env": settings.APP_ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "upload_max_size_mb": settings.UPLOAD_MAX_SIZE_MB,
        "upload_allowed_extensions": settings.UPLOAD_ALLOWED_EXTENSIONS,
    }


@router.get("/api/v1/system/health")
async def system_health():
    """Detailed system health check with dependency status and latency."""
    db_ok, db_latency = await _check_database()
    llm_ok, llm_info = await _check_llm()

    overall = "healthy" if (db_ok and llm_ok) else "degraded" if (db_ok or llm_ok) else "unhealthy"
    return {
        "status": overall,
        "version": "0.1.0",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "dependencies": {
            "database": {
                "status": "ok" if db_ok else "error",
                "latency_ms": db_latency,
            },
            "llm": {
                "status": "ok" if llm_ok else "error",
                "provider": settings.LLM_PROVIDER,
                **llm_info,
            },
        },
    }
