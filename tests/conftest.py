import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  ensures every model is registered on Base.metadata
from app.api.deps import get_db
from app.core.database import Base
from app.kafka.producer import EventPublisher, get_event_publisher
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


class FakeEventPublisher(EventPublisher):
    """Records published events in memory instead of talking to Kafka."""

    def __init__(self) -> None:
        super().__init__(bootstrap_servers="unused")
        self.published: list[tuple[str, object]] = []

    def publish(self, topic, payload, key=None) -> bool:  # noqa: D102
        self.published.append((topic, payload))
        return True


@pytest.fixture()
def db_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine) -> Session:
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fake_event_publisher() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def client(db_session, fake_event_publisher):
    def override_get_db():
        yield db_session

    def override_get_event_publisher():
        return fake_event_publisher

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_event_publisher] = override_get_event_publisher

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
