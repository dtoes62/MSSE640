"""
GraphQL schema — four query resolvers that wrap Week1 triangle logic via bridge.py.

Queries
-------
allValidations(a, b, c)   → TriangleAnalysisResult  (validate + classify, all fields)
triangleType(a, b, c)     → TriangleTypeResult       (type string only)
validateTriangle(a, b, c) → ValidateResult            (boolean validity only)
classifyTriangle(a, b, c) → ClassifyResult            (classification string only)

All queries accept Float arguments and never raise — errors are returned as
structured result fields rather than GraphQL errors so clients can always
inspect a typed response.
"""
from typing import Optional

import strawberry

import bridge


# ---------------------------------------------------------------------------
# Return types
# ---------------------------------------------------------------------------

@strawberry.type
class TriangleAnalysisResult:
    """Full analysis result — mirrors the Week1 REST response shape."""
    valid: bool
    triangle_type: Optional[str]
    message: str


@strawberry.type
class TriangleTypeResult:
    """Returns only the triangle type (or None on error) plus a message."""
    triangle_type: Optional[str]
    message: str


@strawberry.type
class ValidateResult:
    """Returns only the boolean validity result plus a message."""
    valid: bool
    message: str


@strawberry.type
class ClassifyResult:
    """Returns only the classification string (or None on error) plus a message."""
    classification: Optional[str]
    message: str


# ---------------------------------------------------------------------------
# Query resolvers
# ---------------------------------------------------------------------------

@strawberry.type
class Query:

    @strawberry.field(
        description=(
            "Run a full triangle analysis: validate the sides and classify the triangle. "
            "Returns valid, triangleType, and a descriptive message."
        )
    )
    def all_validations(self, a: float, b: float, c: float) -> TriangleAnalysisResult:
        try:
            bridge.validate_triangle(a, b, c)
            t_type = bridge.classify_triangle(a, b, c)
            return TriangleAnalysisResult(
                valid=True,
                triangle_type=t_type,
                message=f"Valid {t_type} triangle.",
            )
        except (bridge.InvalidSideLengthError, bridge.NotATriangleError) as exc:
            return TriangleAnalysisResult(valid=False, triangle_type=None, message=str(exc))

    @strawberry.field(
        description=(
            "Return only the triangle type ('equilateral', 'isosceles', 'scalene') "
            "for valid input, or None with an error message for invalid input."
        )
    )
    def triangle_type(self, a: float, b: float, c: float) -> TriangleTypeResult:
        try:
            bridge.validate_triangle(a, b, c)
            t_type = bridge.classify_triangle(a, b, c)
            return TriangleTypeResult(triangle_type=t_type, message=f"Valid {t_type} triangle.")
        except (bridge.InvalidSideLengthError, bridge.NotATriangleError) as exc:
            return TriangleTypeResult(triangle_type=None, message=str(exc))

    @strawberry.field(
        description=(
            "Return only whether the three sides form a valid triangle. "
            "Does not classify — use allValidations or classifyTriangle for the type."
        )
    )
    def validate_triangle(self, a: float, b: float, c: float) -> ValidateResult:
        try:
            bridge.validate_triangle(a, b, c)
            return ValidateResult(valid=True, message="Triangle is valid.")
        except (bridge.InvalidSideLengthError, bridge.NotATriangleError) as exc:
            return ValidateResult(valid=False, message=str(exc))

    @strawberry.field(
        description=(
            "Return only the triangle classification. "
            "Validates the sides first (classify_triangle assumes valid input). "
            "Returns None with an error message if the sides are invalid."
        )
    )
    def classify_triangle(self, a: float, b: float, c: float) -> ClassifyResult:
        try:
            bridge.validate_triangle(a, b, c)
            classification = bridge.classify_triangle(a, b, c)
            return ClassifyResult(
                classification=classification,
                message=f"Classification: {classification}.",
            )
        except (bridge.InvalidSideLengthError, bridge.NotATriangleError) as exc:
            return ClassifyResult(classification=None, message=str(exc))
