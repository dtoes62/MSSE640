"""
Tests for the four GraphQL queries.

All tests send valid auth headers; auth enforcement is tested in test_auth.py.
"""
import pytest
from tests.conftest import gql


# ---------------------------------------------------------------------------
# AllValidations
# ---------------------------------------------------------------------------

class TestAllValidations:
    _Q = "query A($a:Float!,$b:Float!,$c:Float!){ allValidations(a:$a,b:$b,c:$c){ valid triangleType message } }"

    def test_scalene_triangle(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 3, "b": 4, "c": 5})
        data = resp.json()["data"]["allValidations"]
        assert data["valid"] is True
        assert data["triangleType"] == "scalene"
        assert "scalene" in data["message"]

    def test_equilateral_triangle(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 5, "b": 5, "c": 5})
        data = resp.json()["data"]["allValidations"]
        assert data["valid"] is True
        assert data["triangleType"] == "equilateral"

    def test_isosceles_triangle(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 5, "b": 5, "c": 3})
        data = resp.json()["data"]["allValidations"]
        assert data["valid"] is True
        assert data["triangleType"] == "isosceles"

    def test_zero_side_returns_invalid(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 0, "b": 4, "c": 5})
        data = resp.json()["data"]["allValidations"]
        assert data["valid"] is False
        assert data["triangleType"] is None
        assert data["message"]

    def test_negative_side_returns_invalid(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": -1, "b": 4, "c": 5})
        data = resp.json()["data"]["allValidations"]
        assert data["valid"] is False

    def test_degenerate_triangle_returns_invalid(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 1, "b": 2, "c": 10})
        data = resp.json()["data"]["allValidations"]
        assert data["valid"] is False
        assert data["triangleType"] is None


# ---------------------------------------------------------------------------
# TriangleType
# ---------------------------------------------------------------------------

class TestTriangleType:
    _Q = "query T($a:Float!,$b:Float!,$c:Float!){ triangleType(a:$a,b:$b,c:$c){ triangleType message } }"

    def test_valid_triangle_returns_type(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 3, "b": 4, "c": 5})
        data = resp.json()["data"]["triangleType"]
        assert data["triangleType"] == "scalene"

    def test_invalid_triangle_returns_null_type(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 1, "b": 2, "c": 10})
        data = resp.json()["data"]["triangleType"]
        assert data["triangleType"] is None
        assert data["message"]

    def test_equilateral_type(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 7, "b": 7, "c": 7})
        data = resp.json()["data"]["triangleType"]
        assert data["triangleType"] == "equilateral"


# ---------------------------------------------------------------------------
# ValidateTriangle
# ---------------------------------------------------------------------------

class TestValidateTriangle:
    _Q = "query V($a:Float!,$b:Float!,$c:Float!){ validateTriangle(a:$a,b:$b,c:$c){ valid message } }"

    def test_valid_triangle(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 3, "b": 4, "c": 5})
        data = resp.json()["data"]["validateTriangle"]
        assert data["valid"] is True
        assert data["message"]

    def test_zero_side(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 0, "b": 4, "c": 5})
        data = resp.json()["data"]["validateTriangle"]
        assert data["valid"] is False

    def test_triangle_inequality_failure(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 1, "b": 1, "c": 100})
        data = resp.json()["data"]["validateTriangle"]
        assert data["valid"] is False

    def test_all_permutations_of_valid_345(self, client, auth_headers):
        sides = [3.0, 4.0, 5.0]
        import itertools
        for a, b, c in itertools.permutations(sides):
            resp = gql(client, auth_headers, self._Q, {"a": a, "b": b, "c": c})
            data = resp.json()["data"]["validateTriangle"]
            assert data["valid"] is True, f"Expected valid for ({a}, {b}, {c})"


# ---------------------------------------------------------------------------
# ClassifyTriangle
# ---------------------------------------------------------------------------

class TestClassifyTriangle:
    _Q = "query C($a:Float!,$b:Float!,$c:Float!){ classifyTriangle(a:$a,b:$b,c:$c){ classification message } }"

    def test_scalene(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 3, "b": 4, "c": 5})
        data = resp.json()["data"]["classifyTriangle"]
        assert data["classification"] == "scalene"

    def test_equilateral(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 6, "b": 6, "c": 6})
        data = resp.json()["data"]["classifyTriangle"]
        assert data["classification"] == "equilateral"

    def test_isosceles(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 5, "b": 5, "c": 8})
        data = resp.json()["data"]["classifyTriangle"]
        assert data["classification"] == "isosceles"

    def test_invalid_input_returns_null_classification(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 0, "b": 4, "c": 5})
        data = resp.json()["data"]["classifyTriangle"]
        assert data["classification"] is None
        assert data["message"]

    def test_impossible_triangle_returns_null(self, client, auth_headers):
        resp = gql(client, auth_headers, self._Q, {"a": 1, "b": 2, "c": 100})
        data = resp.json()["data"]["classifyTriangle"]
        assert data["classification"] is None


# ---------------------------------------------------------------------------
# Schema introspection (verifies all four query fields are exposed)
# ---------------------------------------------------------------------------

class TestIntrospection:
    def test_schema_exposes_all_four_queries(self, client, auth_headers):
        introspect = """
        {
          __schema {
            queryType {
              fields { name }
            }
          }
        }
        """
        resp = gql(client, auth_headers, introspect)
        field_names = {f["name"] for f in resp.json()["data"]["__schema"]["queryType"]["fields"]}
        assert "allValidations" in field_names
        assert "triangleType" in field_names
        assert "validateTriangle" in field_names
        assert "classifyTriangle" in field_names
