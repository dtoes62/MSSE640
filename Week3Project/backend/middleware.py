"""
AuditAuthMiddleware — a single Starlette BaseHTTPMiddleware that:

1. Enforces JWT Bearer auth on POST /graphql requests.
2. Logs every request (auth and non-auth paths) to the SQLite audit table.

Auth bypass (no token required):
  GET  /graphql          — lets GraphiQL HTML load in the browser
  POST /auth/token       — the token-issuance endpoint itself
  GET  /docs             — Swagger UI
  GET  /redoc            — ReDoc
  GET  /openapi.json     — OpenAPI spec

All other /graphql traffic (i.e. POST) requires Authorization: Bearer <token>.
  POST /graphql (introspection) — schema introspection queries bypass auth so
                                  GraphiQL can load the Docs panel without a token.
"""
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import auth as auth_module
import database


# Regex fallback for extracting the operation name when operationName is absent.
_OP_NAME_RE = re.compile(r'(?:query|mutation|subscription)\s+(\w+)', re.IGNORECASE)

_AUTH_BYPASS_PATHS = {"/auth/token", "/docs", "/redoc", "/openapi.json"}


def _is_introspection_query(raw_body: bytes) -> bool:
    """Return True if the request body is a GraphQL introspection query."""
    try:
        query = json.loads(raw_body).get("query", "")
        return "__schema" in query or "__type" in query
    except Exception:
        return False


def _is_auth_required(request: Request, raw_body: bytes = b"") -> bool:
    """Return True for POST /graphql requests that are not introspection queries."""
    if not (request.url.path.startswith("/graphql") and request.method == "POST"):
        return False
    return not _is_introspection_query(raw_body)


def _sanitize_headers(headers: dict) -> dict:
    """Return a copy of *headers* with the Authorization value redacted."""
    return {
        k: ("[REDACTED]" if k.lower() == "authorization" else v)
        for k, v in headers.items()
    }


def _parse_query_name(raw_body: bytes) -> Optional[str]:
    try:
        parsed = json.loads(raw_body)
        op_name = parsed.get("operationName")
        if op_name:
            return op_name
        query_str = parsed.get("query", "")
        match = _OP_NAME_RE.search(query_str)
        return match.group(1) if match else None
    except Exception:
        return None


def _parse_input_data(raw_body: bytes) -> Optional[str]:
    try:
        parsed = json.loads(raw_body)
        variables = parsed.get("variables")
        return json.dumps(variables) if variables is not None else None
    except Exception:
        return None


def _parse_output_data(response_body: str) -> Optional[str]:
    try:
        data = json.loads(response_body).get("data")
        return json.dumps(data) if data is not None else None
    except Exception:
        return None


class AuditAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = str(uuid.uuid4())
        received_at = datetime.now(timezone.utc).isoformat()

        # Buffer request body — Starlette caches after the first read.
        raw_body = await request.body()

        # ------------------------------------------------------------------
        # Auth enforcement (POST /graphql only)
        # ------------------------------------------------------------------
        caller_id = "anonymous"

        if _is_auth_required(request, raw_body):
            auth_header = request.headers.get("authorization", "")
            if not auth_header.lower().startswith("bearer "):
                return self._build_401(
                    request_id, caller_id, received_at, raw_body,
                    start, request, "Missing Authorization header.",
                )
            token = auth_header[7:]  # strip "Bearer "
            try:
                payload = auth_module.verify_token(token)
                caller_id = payload.get("sub", "unknown")
            except JWTError:
                return self._build_401(
                    request_id, caller_id, received_at, raw_body,
                    start, request, "Invalid or expired token.",
                )

        # ------------------------------------------------------------------
        # Forward to application
        # ------------------------------------------------------------------
        response = await call_next(request)

        # ------------------------------------------------------------------
        # Buffer response body (body_iterator is a stream; must be consumed)
        # ------------------------------------------------------------------
        body_chunks = []
        async for chunk in response.body_iterator:
            body_chunks.append(chunk)
        response_bytes = b"".join(body_chunks)
        response_body_str = response_bytes.decode("utf-8", errors="replace")

        # ------------------------------------------------------------------
        # Write audit record
        # ------------------------------------------------------------------
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        database.log_request(
            database.AuditRecord(
                request_id=request_id,
                caller_id=caller_id,
                datetime_received=received_at,
                query_name=_parse_query_name(raw_body),
                input_data=_parse_input_data(raw_body),
                output_data=_parse_output_data(response_body_str),
                request_headers=json.dumps(_sanitize_headers(dict(request.headers))),
                request_body=raw_body.decode("utf-8", errors="replace"),
                response_body=response_body_str,
                duration_ms=duration_ms,
            )
        )

        # Rebuild response — the original body_iterator is now exhausted.
        return Response(
            content=response_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    def _build_401(
        self,
        request_id: str,
        caller_id: str,
        received_at: str,
        raw_body: bytes,
        start: float,
        request: Request,
        detail: str,
    ) -> JSONResponse:
        error_body = json.dumps({"detail": detail})
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        database.log_request(
            database.AuditRecord(
                request_id=request_id,
                caller_id=caller_id,
                datetime_received=received_at,
                query_name=_parse_query_name(raw_body),
                input_data=_parse_input_data(raw_body),
                output_data=None,
                request_headers=json.dumps(_sanitize_headers(dict(request.headers))),
                request_body=raw_body.decode("utf-8", errors="replace"),
                response_body=error_body,
                duration_ms=duration_ms,
            )
        )
        return JSONResponse({"detail": detail}, status_code=401)
