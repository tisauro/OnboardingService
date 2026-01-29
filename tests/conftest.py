import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.db.database import Base
from app.core.settings import get_settings
from app.main import app
from tests.async_db_utils import create_database_async, drop_database_async

# Use a separate test database
orig_settings = get_settings()
TEST_DATABASE_URL = orig_settings.sqlalchemy_postgres_uri.unicode_string().replace(
    f"/{orig_settings.postgres_db}", "/test_db"
)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    await create_database_async(TEST_DATABASE_URL)
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    if "test" in TEST_DATABASE_URL.lower():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
        await drop_database_async(TEST_DATABASE_URL)
    else:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_maker = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def override_get_db(db_session):
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
