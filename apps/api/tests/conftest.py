from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.api.routes import auth, health, plans, profile
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.services.seed import seed_catalog


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    source_url = make_url(get_settings().database_url)
    admin_url = source_url.set(database="postgres")
    database_name = f"fitplan_test_{uuid4().hex[:10]}"

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))

    engine = create_engine(
        source_url.set(database=database_name),
        pool_pre_ping=True,
    )

    Base.metadata.create_all(bind=engine)

    seed_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    with seed_session_factory() as session:
        seed_catalog(session)

    yield engine

    engine.dispose()

    with admin_engine.connect() as connection:
        connection.execute(
            text(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :database_name
                  AND pid <> pg_backend_pid()
                """
            ),
            {"database_name": database_name},
        )
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))

    admin_engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    testing_session_factory = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = testing_session_factory()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    test_app = FastAPI()
    prefix = get_settings().api_v1_prefix

    test_app.include_router(health.router, prefix=prefix)
    test_app.include_router(auth.router, prefix=prefix)
    test_app.include_router(profile.router, prefix=prefix)
    test_app.include_router(plans.router, prefix=prefix)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client
