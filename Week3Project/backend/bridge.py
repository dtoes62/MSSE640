"""
Bridge module — imports triangle logic from Week1Project without modifying it.

This is the ONLY file in Week3Project that touches sys.path.
All other modules that need triangle functions import from here.
"""
import os
import sys

_WEEK1_BACKEND = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Week1Project", "backend")
)
if _WEEK1_BACKEND not in sys.path:
    sys.path.insert(0, _WEEK1_BACKEND)

# These imports resolve against Week1Project/backend/ once the path is injected.
from triangle import validate_triangle, classify_triangle  # noqa: E402
from exceptions import (  # noqa: E402
    InvalidSideLengthError,
    NotATriangleError,
    NonNumericInputError,
)

__all__ = [
    "validate_triangle",
    "classify_triangle",
    "InvalidSideLengthError",
    "NotATriangleError",
    "NonNumericInputError",
]
