class TriangleError(Exception):
    """Base class for all triangle-related errors."""
    pass


class InvalidSideLengthError(TriangleError):
    """Raised when a side length is zero or negative."""
    def __init__(self, side_name: str, value: float):
        self.side_name = side_name
        self.value = value
        super().__init__(
            f"Side '{side_name}' has an invalid value ({value}). "
            "All sides must be greater than zero."
        )


class NonNumericInputError(TriangleError, ValueError):
    """Raised when a side value cannot be interpreted as a number.

    Inherits from ValueError so Pydantic validators recognize it
    and return a 422 Unprocessable Entity response.
    """
    def __init__(self, side_name: str, value):
        self.side_name = side_name
        self.value = value
        super().__init__(
            f"Side '{side_name}' received a non-numeric value: '{value}'."
        )


class NotATriangleError(TriangleError):
    """Raised when the three sides do not satisfy the triangle inequality."""
    def __init__(self, a: float, b: float, c: float):
        self.sides = (a, b, c)
        super().__init__(
            f"Sides ({a}, {b}, {c}) do not form a valid triangle. "
            "The sum of any two sides must be strictly greater than the third."
        )
