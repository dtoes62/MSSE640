import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from triangle import validate_triangle, classify_triangle
from exceptions import InvalidSideLengthError, NotATriangleError


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidateTriangle:

    def test_valid_triangle_returns_true(self):
        """A basic valid triangle should return True."""
        assert validate_triangle(3, 4, 5) is True

    def test_zero_side_raises_invalid_length(self):
        """A side of zero must raise InvalidSideLengthError."""
        with pytest.raises(InvalidSideLengthError):
            validate_triangle(0, 4, 5)

    def test_negative_side_raises_invalid_length(self):
        """A negative side must raise InvalidSideLengthError."""
        with pytest.raises(InvalidSideLengthError):
            validate_triangle(-1, 4, 5)

    def test_zero_side_exception_contains_side_name(self):
        """The exception should identify which side was invalid."""
        with pytest.raises(InvalidSideLengthError) as exc_info:
            validate_triangle(3, 0, 5)
        assert exc_info.value.side_name == "b"

    def test_degenerate_triangle_raises_not_a_triangle(self):
        """Sides where a + b == c (1, 2, 3) are degenerate — not valid."""
        with pytest.raises(NotATriangleError):
            validate_triangle(1, 2, 3)

    def test_impossible_triangle_raises_not_a_triangle(self):
        """Sides where one is far larger than the other two are not valid."""
        with pytest.raises(NotATriangleError):
            validate_triangle(1, 1, 10)

    def test_not_a_triangle_exception_stores_sides(self):
        """The exception should store the side values that caused the failure."""
        with pytest.raises(NotATriangleError) as exc_info:
            validate_triangle(1, 2, 3)
        assert exc_info.value.sides == (1, 2, 3)


# ---------------------------------------------------------------------------
# Classification tests
# ---------------------------------------------------------------------------

class TestClassifyTriangle:

    def test_equilateral(self):
        assert classify_triangle(3, 3, 3) == "equilateral"

    def test_isosceles_ab_equal(self):
        assert classify_triangle(5, 5, 3) == "isosceles"

    def test_isosceles_bc_equal(self):
        assert classify_triangle(3, 5, 5) == "isosceles"

    def test_isosceles_ac_equal(self):
        assert classify_triangle(5, 3, 5) == "isosceles"

    def test_scalene(self):
        assert classify_triangle(3, 4, 5) == "scalene"


# ---------------------------------------------------------------------------
# Scalene permutation tests (Myers Chapter 1)
# ---------------------------------------------------------------------------

class TestScalenePermutations:
    """
    Myers points out that a correct implementation must handle sides
    in any order. These six tests cover every permutation of (3, 4, 5).
    """

    SIDES = (3, 4, 5)

    def _permutations(self):
        a, b, c = self.SIDES
        return [
            (a, b, c),
            (a, c, b),
            (b, a, c),
            (b, c, a),
            (c, a, b),
            (c, b, a),
        ]

    def test_all_permutations_are_valid(self):
        for a, b, c in self._permutations():
            assert validate_triangle(a, b, c) is True, f"Failed for ({a}, {b}, {c})"

    def test_all_permutations_are_scalene(self):
        for a, b, c in self._permutations():
            assert classify_triangle(a, b, c) == "scalene", f"Failed for ({a}, {b}, {c})"
