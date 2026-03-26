"""
Test configuration — runs automatically before any test in the suite.

The problem this solves:
  Our app's init_db() lives inside a FastAPI lifespan handler, which only
  fires when TestClient is used as a context manager (with TestClient(...)).
  Since we create the TestClient at module level, the lifespan never runs
  in CI — so the database tables don't exist and every DB call returns 500.

The fix:
  A session-scoped autouse fixture that calls init_db() once before all
  tests. "session" scope means it runs exactly once for the entire test run.
  "autouse=True" means it applies to every test automatically.
"""

import pytest
from app.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all database tables before the test suite starts."""
    init_db()
