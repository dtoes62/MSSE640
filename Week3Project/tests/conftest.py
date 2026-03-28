"""
Shared fixtures for Week3 tests.

Overrides SQLITE_DB_PATH before any module imports database so that tests
write to a temporary file and never touch the real audit.db.
"""
import os
import sys
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Ensure the backend package is importable when pytest is run from any cwd.
# ---------------------------------------------------------------------------
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ---------------------------------------------------------------------------
# Override DB path BEFORE importing config / database / app.
# ---------------------------------------------------------------------------
import config  # noqa: E402  (must come after sys.path manipulation)

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
config.SQLITE_DB_PATH = _tmp_db.name


# Now safe to import the app.
from main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from auth import create_access_token  # noqa: E402
import database  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    database.init_db()
    yield
    try:
        os.unlink(config.SQLITE_DB_PATH)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def valid_token():
    return create_access_token({"sub": "test_user"})


@pytest.fixture(scope="session")
def auth_headers(valid_token):
    return {"Authorization": f"Bearer {valid_token}"}


# ---------------------------------------------------------------------------
# Helper used by graphql test modules
# ---------------------------------------------------------------------------
def gql(client, headers, query: str, variables=None):
    """Post a GraphQL request and return the Response."""
    return client.post(
        "/graphql",
        json={"query": query, "variables": variables or {}, "operationName": None},
        headers=headers,
    )
