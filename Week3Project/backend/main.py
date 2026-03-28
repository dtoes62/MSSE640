"""
Triangle GraphQL API — Week3Project entry point.

Endpoints
---------
POST /auth/token     — obtain a JWT (Swagger UI at /docs)
GET  /graphql        — GraphiQL IDE (loads without auth)
POST /graphql        — GraphQL endpoint (requires Authorization: Bearer <token>)
GET  /docs           — Swagger UI (REST endpoints only)
GET  /redoc          — ReDoc

Startup
-------
uvicorn main:app --reload --port 8001
"""
from contextlib import asynccontextmanager

import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

import database
from auth import auth_router
from middleware import AuditAuthMiddleware
from schema import Query


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema, graphql_ide="graphiql")

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
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit + auth middleware (runs after CORS, before routing).
app.add_middleware(AuditAuthMiddleware)

app.include_router(auth_router, prefix="/auth")
app.include_router(graphql_app, prefix="/graphql")
