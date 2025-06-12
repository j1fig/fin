"""
Pytest configuration and fixtures for testing.
"""

import pytest
from sqlmodel import SQLModel, create_engine, Session
from fin.repositories.factory import RepositoryFactory


@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session
        # Rollback any uncommitted changes after each test
        session.rollback()


@pytest.fixture
def repository_factory(test_session):
    """Create a repository factory with test session."""
    return RepositoryFactory(test_session) 