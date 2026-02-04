import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.core.crud import bootstrap_keys
from app.core.db.database import Base
from app.core.schemas import schemas
from app.core.settings import get_settings
from app.main import app
from tests.async_db_utils import create_database_async, drop_database_async

# Use a separate test database
orig_settings = get_settings()
TEST_DATABASE_URL = orig_settings.sqlalchemy_postgres_uri.unicode_string().replace(
    f"/{orig_settings.postgres_db}", "/test_db"
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create/drop the test DB once per test run (fast).
    """
    await create_database_async(TEST_DATABASE_URL)
    engine = create_async_engine(TEST_DATABASE_URL, echo=True, future=True, poolclass=NullPool)
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


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """
    One session per test, isolated via SAVEPOINT so tests see an "empty DB"
    even if the code under test calls commit().
    """
    async with test_engine.connect() as connection:
        """
        outer transaction:
        - started by the fixture
        - never committed
        - rolled back at the end of the test → wipes everything done in the test
        """
        outer = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        # Start a SAVEPOINT (nested transaction)
        await session.begin_nested()

        # If production code commits, restart the SAVEPOINT automatically.
        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess, transaction):
            if transaction.nested and not transaction._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()


@pytest_asyncio.fixture(autouse=True)
async def override_get_db(db_session):
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seed_bootstrap_keys_20(db_session):
    keys_data = []
    for i in range(20):
        key = schemas.BootstrapKeyCreateRequest(group=f"group-{i}")
        await bootstrap_keys.create_key(db_session, key)
        keys_data.append(key)
    yield keys_data


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
