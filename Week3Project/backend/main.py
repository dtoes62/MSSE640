"""
Triangle GraphQL API — Week3Project entry point.

Endpoints
---------
POST /auth/token     — obtain a JWT (Swagger UI at /docs)
GET  /graphql        — custom GraphiQL IDE (auto-fetches token on login)
POST /graphql        — GraphQL endpoint (requires Authorization: Bearer <token>)
GET  /docs           — Swagger UI (REST endpoints only)
GET  /redoc          — ReDoc

Startup
-------
uvicorn main:app --port 8443 --ssl-certfile ../certs/cert.pem --ssl-keyfile ../certs/key.pem
"""
import os
from contextlib import asynccontextmanager

import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter

import database
from auth import auth_router
from middleware import AuditAuthMiddleware
from schema import Query

_GRAPHIQL_HTML = open(
    os.path.join(os.path.dirname(__file__), "graphiql.html"), encoding="utf-8"
).read()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


schema = strawberry.Schema(query=Query)
# graphql_ide=None — we serve our own IDE via the GET /graphql route below.
graphql_app = GraphQLRouter(schema, graphql_ide=None)

app = FastAPI(
    title="Triangle GraphQL API",
    description=(
        "GraphQL API wrapping Week1 triangle analysis logic. "
        "Authenticate via POST /auth/token, then use the Bearer token in GraphQL requests. "
        "Interactive GraphQL IDE: GET /graphql — Interactive REST docs: GET /docs"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow local frontend dev servers to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://localhost:8443",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit + auth middleware (runs after CORS, before routing).
app.add_middleware(AuditAuthMiddleware)

app.include_router(auth_router, prefix="/auth")


# Custom GraphiQL IDE — must be registered BEFORE GraphQLRouter so this GET
# handler takes precedence over Strawberry's (now disabled) IDE route.
@app.get("/graphql", include_in_schema=False)
async def graphiql_ide():
    return HTMLResponse(_GRAPHIQL_HTML)


app.include_router(graphql_app, prefix="/graphql")
