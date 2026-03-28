"""
Tests for SQLite audit logging.

Each test makes a live request through the TestClient and then inspects the
most-recently-written audit_log row to verify the middleware populated it correctly.
"""
import json
import sqlite3

import pytest

import config
from tests.conftest import gql

_VALID_Q = "query CheckAudit($a:Float!,$b:Float!,$c:Float!){ allValidations(a:$a,b:$b,c:$c){ valid triangleType message } }"
_VARS = {"a": 3, "b": 4, "c": 5}


def _last_row() -> dict:
    con = sqlite3.connect(config.SQLITE_DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else {}
    finally:
        con.close()


class TestAuditRowWritten:
    def test_row_written_after_query(self, client, auth_headers):
        before_count = sqlite3.connect(config.SQLITE_DB_PATH).execute(
            "SELECT COUNT(*) FROM audit_log"
        ).fetchone()[0]
        gql(client, auth_headers, _VALID_Q, _VARS)
        after_count = sqlite3.connect(config.SQLITE_DB_PATH).execute(
            "SELECT COUNT(*) FROM audit_log"
        ).fetchone()[0]
        assert after_count == before_count + 1

    def test_row_has_unique_request_id(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["request_id"]
        assert len(row["request_id"]) == 36  # UUID format

    def test_caller_id_matches_token_sub(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["caller_id"] == "test_user"

    def test_datetime_received_is_iso_format(self, client, auth_headers):
        from datetime import datetime
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        # Should parse without error.
        datetime.fromisoformat(row["datetime_received"])

    def test_duration_ms_is_positive(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["duration_ms"] > 0


class TestAuditFieldContent:
    def test_input_data_contains_variables(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["input_data"] is not None
        parsed = json.loads(row["input_data"])
        assert parsed["a"] == 3
        assert parsed["b"] == 4
        assert parsed["c"] == 5

    def test_output_data_reflects_valid_response(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["output_data"] is not None
        parsed = json.loads(row["output_data"])
        assert parsed["allValidations"]["valid"] is True

    def test_authorization_header_value_is_redacted(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        headers = json.loads(row["request_headers"])
        auth_value = headers.get("authorization", "")
        # The value must be redacted; the actual token must not appear.
        token = auth_headers["Authorization"].split(" ", 1)[1]
        assert token not in auth_value
        assert auth_value == "[REDACTED]"

    def test_request_body_is_stored(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["request_body"]
        parsed = json.loads(row["request_body"])
        assert "query" in parsed

    def test_response_body_is_stored(self, client, auth_headers):
        gql(client, auth_headers, _VALID_Q, _VARS)
        row = _last_row()
        assert row["response_body"]
        parsed = json.loads(row["response_body"])
        assert "data" in parsed


class TestAuditOnRejectedRequest:
    def test_401_request_is_also_logged(self, client):
        """Rejected (unauthenticated) requests should still produce an audit row."""
        con = sqlite3.connect(config.SQLITE_DB_PATH)
        before = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        con.close()

        client.post("/graphql", json={"query": _VALID_Q, "variables": _VARS})

        con = sqlite3.connect(config.SQLITE_DB_PATH)
        after = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        con.close()
        assert after == before + 1

    def test_401_row_has_anonymous_caller_id(self, client):
        client.post("/graphql", json={"query": _VALID_Q, "variables": _VARS})
        row = _last_row()
        assert row["caller_id"] == "anonymous"
