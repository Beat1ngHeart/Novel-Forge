import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analyses,
    bible,
    bible_candidates,
    chapter_plans,
    chapters,
    creative,
    documents,
    draft_versions,
    drafts,
    projects,
    providers,
    rhythms,
    state_changes,
    synopses,
    system,
    tasks,
    volumes,
)
from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler, generic_error_handler
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    # Create tables if they don't exist (dev convenience)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified")
    except Exception as e:
        logger.warning("Database not available at startup: %s", e)
        logger.warning("The API will start but database operations will fail until PostgreSQL is available")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Routes
app.include_router(system.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(chapters.router)
app.include_router(providers.router)
app.include_router(analyses.router)
app.include_router(tasks.router)
app.include_router(bible.characters)
app.include_router(bible.world_rules)
app.include_router(bible.plot_threads)
app.include_router(bible.foreshadowings)
app.include_router(creative.router)
app.include_router(bible_candidates.router)
app.include_router(synopses.router)
app.include_router(volumes.router)
app.include_router(rhythms.router)
app.include_router(chapter_plans.router)
app.include_router(drafts.router)
app.include_router(draft_versions.router)
app.include_router(state_changes.router)
