from exceptions import InvalidSideLengthError, NotATriangleError


def validate_triangle(a: float, b: float, c: float) -> bool:
    """
    Validate that three sides can form a triangle.

    Raises:
        InvalidSideLengthError: if any side is zero or negative.
        NotATriangleError: if the sides fail the triangle inequality theorem.

    Returns:
        True if valid.
    """
    for name, value in [("a", a), ("b", b), ("c", c)]:
        if value <= 0:
            raise InvalidSideLengthError(name, value)

    if (a + b <= c) or (a + c <= b) or (b + c <= a):
        raise NotATriangleError(a, b, c)

    return True


def classify_triangle(a: float, b: float, c: float) -> str:
    """
    Classify a triangle as equilateral, isosceles, or scalene.

    Assumes the sides have already been validated.

    Returns:
        One of: 'equilateral', 'isosceles', 'scalene'
    """
    if a == b == c:
        return "equilateral"
    if a == b or b == c or a == c:
        return "isosceles"
    return "scalene"
