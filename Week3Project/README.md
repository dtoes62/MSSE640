# Week3Project — Triangle GraphQL API

A GraphQL API that wraps the triangle analysis logic from Week1Project. Built with FastAPI and Strawberry, secured with JWT authentication, and served over HTTPS with HTTP/2.

---

## Features

- **GraphQL API** with four queries covering triangle validation and classification
- **JWT Bearer authentication** — short-lived tokens (30 min), auto-enforced on all queries
- **HTTPS + HTTP/2** — TLS via self-signed certificate, HTTP/2 via the `h2` package
- **SQLite audit logging** — every request is logged with caller identity, I/O, headers, timestamps, and duration
- **Custom GraphiQL IDE** — browser-based explorer with built-in login flow and live token countdown
- **Swagger UI** — interactive REST docs for the auth endpoint
- **Postman collection** — pre-built requests for all four queries plus error cases
- **98% test coverage** — 41 tests across auth, GraphQL queries, and audit logging

---

## GraphQL Queries

All queries accept three `Float` arguments: `a`, `b`, `c` (the triangle side lengths).

| Query | Returns | Description |
|---|---|---|
| `allValidations` | `valid`, `triangleType`, `message` | Full analysis — validates and classifies |
| `triangleType` | `triangleType`, `message` | Triangle type only (`equilateral`, `isosceles`, `scalene`) |
| `validateTriangle` | `valid`, `message` | Boolean validity check only |
| `classifyTriangle` | `classification`, `message` | Classification only |

Example:

```graphql
query {
  allValidations(a: 3, b: 4, c: 5) {
    valid
    triangleType
    message
  }
}
```

---

## Project Structure

```
Week3Project/
├── backend/
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # JWT, database, and TLS settings
│   ├── bridge.py        # Imports triangle logic from Week1Project
│   ├── schema.py        # GraphQL schema and resolvers
│   ├── auth.py          # JWT token creation and /auth/token endpoint
│   ├── database.py      # SQLite audit log
│   ├── middleware.py    # Auth enforcement and request logging
│   └── graphiql.html    # Custom GraphiQL IDE
├── certs/
│   ├── cert.pem         # TLS certificate (self-signed)
│   └── key.pem          # TLS private key
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_graphql.py
│   └── test_audit.py
├── Postman/
│   ├── Triangle_GraphQL_API.postman_collection.json
│   └── Triangle_GraphQL_API.postman_environment.json
├── Writeup/
│   └── Week3Writeup.md
├── requirements.txt
└── start.sh
```

---

## Prerequisites

- Python 3.9+
- Week1Project present at `../Week1Project` (triangle logic is imported directly — no Week1 server required)

---

## Local Setup

### 1. Install dependencies

```bash
cd Week3Project
pip install -r requirements.txt
```

### 2. Start the server

```bash
bash start.sh
```

This starts the API over HTTPS on port **8443**. The self-signed certificate is already included in `certs/`.

To use a custom port:

```bash
bash start.sh 9443
```

To start manually:

```bash
cd backend
uvicorn main:app --port 8443 --ssl-certfile ../certs/cert.pem --ssl-keyfile ../certs/key.pem
```

### 3. Accept the self-signed certificate

The first time you open the API in a browser, you will see a security warning. Click **Advanced → Proceed to localhost** to continue. This is expected for a locally self-signed certificate.

For Postman, go to **Settings → General** and disable **SSL certificate verification**.

---

## Usage

### Swagger UI (Auth)

```
https://localhost:8443/docs
```

Use `POST /auth/token` to obtain a JWT. Default credentials:

| Field | Value |
|---|---|
| username | `admin` |
| password | `secret` |

### GraphiQL (Interactive Query Explorer)

```
https://localhost:8443/graphql
```

The IDE opens a login form automatically. Enter your credentials and click **Get Token & Open GraphiQL**. The token is stored in `localStorage` and refreshed on re-login. A countdown in the status bar shows the remaining token lifetime.

### Postman

Import both files from the `Postman/` folder:

- `Triangle_GraphQL_API.postman_collection.json`
- `Triangle_GraphQL_API.postman_environment.json`

Select the **Triangle GraphQL API — Local** environment, run **Auth → Get JWT Token** first, then fire any query.

---

## Running Tests

```bash
cd Week3Project
python -m pytest
```

Runs all 41 tests with coverage report. Tests use a temporary database and never touch `audit.db`.

```bash
python -m pytest tests/test_auth.py     # Auth and JWT enforcement
python -m pytest tests/test_graphql.py  # All four queries
python -m pytest tests/test_audit.py    # Audit log field verification
```

---

## Audit Log

Every request is written to `backend/audit.db` (SQLite). Schema:

| Column | Description |
|---|---|
| `request_id` | UUID per request |
| `caller_id` | JWT `sub` claim (`anonymous` for unauthenticated requests) |
| `datetime_received` | UTC ISO timestamp |
| `query_name` | GraphQL operation name |
| `input_data` | Request variables (JSON) |
| `output_data` | Response data (JSON) |
| `request_headers` | Sanitized headers (`authorization` value redacted) |
| `request_body` | Raw GraphQL request |
| `response_body` | Full response JSON |
| `duration_ms` | Request duration in milliseconds |

The database can be browsed directly in VS Code using the **Database Client** extension (search publisher: Weijan Chen).
