import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import session as db_session_module
from app.db.base import Base


@pytest.fixture(autouse=True)
def _test_db(tmp_path):
    """Override database with in-memory SQLite for tests."""
    import asyncio

    db_file = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{db_file}"
    test_engine = create_async_engine(url)
    test_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def _setup():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup())

    # Patch the module-level references
    original_engine = db_session_module.engine
    original_factory = db_session_module.async_session_factory
    db_session_module.engine = test_engine
    db_session_module.async_session_factory = test_factory

    yield

    db_session_module.engine = original_engine
    db_session_module.async_session_factory = original_factory
