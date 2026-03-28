"""
SQLite audit log — records every request the API receives.

Uses only the stdlib sqlite3 module; no ORM dependency required.
"""
import sqlite3
from dataclasses import dataclass
from typing import Optional

import config


@dataclass
class AuditRecord:
    request_id: str
    caller_id: str
    datetime_received: str
    query_name: Optional[str]
    input_data: Optional[str]
    output_data: Optional[str]
    request_headers: str   # JSON blob (authorization value stripped)
    request_body: str      # raw GraphQL JSON string
    response_body: str     # full response JSON string
    duration_ms: float


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id        TEXT    NOT NULL,
    caller_id         TEXT    NOT NULL,
    datetime_received TEXT    NOT NULL,
    query_name        TEXT,
    input_data        TEXT,
    output_data       TEXT,
    request_headers   TEXT    NOT NULL,
    request_body      TEXT    NOT NULL,
    response_body     TEXT    NOT NULL,
    duration_ms       REAL    NOT NULL
);
"""

_INSERT = """
INSERT INTO audit_log
    (request_id, caller_id, datetime_received, query_name,
     input_data, output_data, request_headers, request_body,
     response_body, duration_ms)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(config.SQLITE_DB_PATH)


def init_db() -> None:
    """Create the audit_log table if it does not already exist."""
    con = _connect()
    try:
        con.execute(_CREATE_TABLE)
        con.commit()
    finally:
        con.close()


def log_request(record: AuditRecord) -> None:
    """Insert one audit row. Silently ignores errors to avoid masking real responses."""
    try:
        con = _connect()
        try:
            con.execute(
                _INSERT,
                (
                    record.request_id,
                    record.caller_id,
                    record.datetime_received,
                    record.query_name,
                    record.input_data,
                    record.output_data,
                    record.request_headers,
                    record.request_body,
                    record.response_body,
                    record.duration_ms,
                ),
            )
            con.commit()
        finally:
            con.close()
    except Exception:
        pass
