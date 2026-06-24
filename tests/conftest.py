import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# ─── In-memory SQLite for tests (no Postgres needed) ─────────────────────────

TEST_DB_URL = "sqlite://"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Reusable payloads ────────────────────────────────────────────────────────

REGISTER_PAYLOAD = {
    "email": "alice@solar.io",
    "username": "alice_solar",
    "password": "Str0ng!Pass",
    "confirm_password": "Str0ng!Pass",
    "full_name": "Alice Dupont",
    "role": "SELLER",
    "wallet_address": "0xAbCd1234567890AbCd1234567890AbCd12345678",
}

