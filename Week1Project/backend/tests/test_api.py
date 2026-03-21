import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

client = TestClient(app)


def post_triangle(a, b, c):
    """Helper to reduce boilerplate in each test."""
    return client.post("/triangle", json={"a": a, "b": b, "c": c})


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestValidTriangles:

    def test_scalene_returns_200(self):
        response = post_triangle(3, 4, 5)
        assert response.status_code == 200

    def test_scalene_is_valid(self):
        data = post_triangle(3, 4, 5).json()
        assert data["valid"] is True
        assert data["triangle_type"] == "scalene"

    def test_equilateral(self):
        data = post_triangle(5, 5, 5).json()
        assert data["valid"] is True
        assert data["triangle_type"] == "equilateral"

    def test_isosceles(self):
        data = post_triangle(5, 5, 3).json()
        assert data["valid"] is True
        assert data["triangle_type"] == "isosceles"

    def test_response_includes_message(self):
        data = post_triangle(3, 4, 5).json()
        assert "message" in data
        assert len(data["message"]) > 0


# ---------------------------------------------------------------------------
# Invalid side lengths
# ---------------------------------------------------------------------------

class TestInvalidSideLengths:

    def test_zero_side_returns_invalid(self):
        data = post_triangle(0, 4, 5).json()
        assert data["valid"] is False

    def test_zero_side_has_message(self):
        data = post_triangle(0, 4, 5).json()
        assert "zero" in data["message"].lower() or "invalid" in data["message"].lower()

    def test_negative_side_returns_invalid(self):
        data = post_triangle(-1, 4, 5).json()
        assert data["valid"] is False

    def test_triangle_type_is_none_when_invalid(self):
        data = post_triangle(0, 4, 5).json()
        assert data["triangle_type"] is None


# ---------------------------------------------------------------------------
# Fails triangle inequality
# ---------------------------------------------------------------------------

class TestNotATriangle:

    def test_degenerate_returns_invalid(self):
        data = post_triangle(1, 2, 3).json()
        assert data["valid"] is False

    def test_impossible_sides_returns_invalid(self):
        data = post_triangle(1, 1, 10).json()
        assert data["valid"] is False


# ---------------------------------------------------------------------------
# Non-numeric input (Pydantic layer)
# ---------------------------------------------------------------------------

class TestNonNumericInput:

    def test_string_side_returns_422(self):
        response = client.post("/triangle", json={"a": "cat", "b": 4, "c": 5})
        assert response.status_code == 422

    def test_missing_field_returns_422(self):
        response = client.post("/triangle", json={"a": 3, "b": 4})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Scalene permutations via API (Myers Chapter 1)
# ---------------------------------------------------------------------------

class TestScalenePermutationsAPI:

    SIDES = (3, 4, 5)

    def _permutations(self):
        a, b, c = self.SIDES
        return [
            (a, b, c), (a, c, b),
            (b, a, c), (b, c, a),
            (c, a, b), (c, b, a),
        ]

    def test_all_permutations_valid(self):
        for a, b, c in self._permutations():
            data = post_triangle(a, b, c).json()
            assert data["valid"] is True, f"Expected valid for ({a},{b},{c})"

    def test_all_permutations_scalene(self):
        for a, b, c in self._permutations():
            data = post_triangle(a, b, c).json()
            assert data["triangle_type"] == "scalene", f"Expected scalene for ({a},{b},{c})"
