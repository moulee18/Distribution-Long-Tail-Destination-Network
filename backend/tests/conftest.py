import os
import sys
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Use SQLite for self-contained deterministic test runs
TEST_DB_URL = "sqlite+aiosqlite:///./test_incubrix.db"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./test_incubrix.db"
os.environ["SIMULATION_MODE"] = "true"

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.connectors.registry import registry

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Also patch AsyncSessionLocal used by background runner so background tasks use the test DB
import backend.app.core.database as db_module
import backend.app.jobs.tasks as tasks_module
db_module.AsyncSessionLocal = TestingSessionLocal
tasks_module.AsyncSessionLocal = TestingSessionLocal

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_environment():
    manifests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "manifests"))
    registry.load_manifests(manifests_dir)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()
    if os.path.exists("./test_incubrix.db"):
        try:
            os.remove("./test_incubrix.db")
        except Exception:
            pass

@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
