"""Row-level tenant isolation tests (Section 11: "tested explicitly — user A
cannot retrieve user B's advisories or knowledge base") need a real Postgres,
since the models use postgres-only column types (UUID, JSONB, ARRAY) that
don't run against SQLite. This sandbox has no Docker, so these tests skip
cleanly here rather than erroring — run them for real with:

    docker compose up -d
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/pipsentry_test \
        pytest apps/api/tests -v
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base
from app.models.advisory import Advisory
from app.models.ingested_source import IngestedSource
from app.models.user import User
from app.models.watchlist import Watchlist


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(settings.database_url)
    try:
        with engine.connect():
            pass
    except Exception as exc:
        pytest.skip(f"No reachable Postgres at {settings.database_url}: {exc}")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(db_engine) -> Session:
    session = sessionmaker(bind=db_engine)()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def two_users(db: Session) -> tuple[User, User]:
    user_a = User(id=uuid.uuid4(), email="a@test.pipsentry", auth_provider_id="auth_a", plan_tier="free")
    user_b = User(id=uuid.uuid4(), email="b@test.pipsentry", auth_provider_id="auth_b", plan_tier="free")
    db.add_all([user_a, user_b])
    db.commit()

    db.add_all(
        [
            Watchlist(id=uuid.uuid4(), user_id=user_a.id, symbol="EURUSD", timeframe="1h"),
            Advisory(
                id=uuid.uuid4(),
                user_id=user_a.id,
                symbol="EURUSD",
                timeframe="1h",
                action="BUY_LIMIT",
                confidence_score=0.8,
                payload_json={"disclaimer": "test"},
            ),
            IngestedSource(
                id=uuid.uuid4(),
                user_id=user_a.id,
                source_type="txt",
                title="User A's strategy notes",
                vector_collection_name=f"kb_{user_a.id}",
            ),
        ]
    )
    db.commit()
    return user_a, user_b
