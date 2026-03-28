"""
Tests for the /auth/token endpoint and JWT enforcement on /graphql.
"""
import time

import pytest
from jose import jwt

import config
from auth import create_access_token
from tests.conftest import gql

VALID_QUERY = "{ allValidations(a: 3, b: 4, c: 5) { valid message } }"


class TestTokenIssuance:
    def test_valid_credentials_return_token(self, client):
        resp = client.post("/auth/token", data={"username": "admin", "password": "secret"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] == config.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_wrong_password_returns_401(self, client):
        resp = client.post("/auth/token", data={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_unknown_user_returns_401(self, client):
        resp = client.post("/auth/token", data={"username": "nobody", "password": "secret"})
        assert resp.status_code == 401

    def test_token_payload_contains_sub(self, client):
        resp = client.post("/auth/token", data={"username": "admin", "password": "secret"})
        token = resp.json()["access_token"]
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        assert payload["sub"] == "admin"


class TestGraphQLAuthEnforcement:
    def test_missing_auth_header_returns_401(self, client):
        resp = client.post("/graphql", json={"query": VALID_QUERY})
        assert resp.status_code == 401

    def test_malformed_token_returns_401(self, client):
        resp = client.post(
            "/graphql",
            json={"query": VALID_QUERY},
            headers={"Authorization": "Bearer not.a.real.token"},
        )
        assert resp.status_code == 401

    def test_wrong_scheme_returns_401(self, client):
        resp = client.post(
            "/graphql",
            json={"query": VALID_QUERY},
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client):
        # Create a token with a past expiry using a raw jose call.
        from datetime import datetime, timedelta, timezone
        expired = jwt.encode(
            {"sub": "test", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM,
        )
        resp = client.post(
            "/graphql",
            json={"query": VALID_QUERY},
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401

    def test_valid_token_reaches_graphql(self, client, auth_headers):
        resp = gql(client, auth_headers, VALID_QUERY)
        assert resp.status_code == 200

    def test_graphiql_loads_without_token(self, client):
        """GET /graphql should serve GraphiQL HTML without any auth."""
        resp = client.get("/graphql", headers={"Accept": "text/html"})
        assert resp.status_code == 200
        assert "graphql" in resp.text.lower()
