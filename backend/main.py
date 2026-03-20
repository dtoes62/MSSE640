from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from exceptions import InvalidSideLengthError, NonNumericInputError, NotATriangleError
from triangle import validate_triangle, classify_triangle

app = FastAPI(title="Triangle Analyzer")

# Allow the React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_methods=["*"],
    allow_headers=["*"],
)


class TriangleRequest(BaseModel):
    a: float
    b: float
    c: float

    @field_validator("a", "b", "c", mode="before")
    @classmethod
    def must_be_numeric(cls, value, info):
        try:
            return float(value)
        except (TypeError, ValueError):
            raise NonNumericInputError(info.field_name, value)


class TriangleResponse(BaseModel):
    valid: bool
    triangle_type: str | None = None
    message: str


@app.post("/triangle", response_model=TriangleResponse)
def analyze_triangle(body: TriangleRequest):
    try:
        validate_triangle(body.a, body.b, body.c)
        triangle_type = classify_triangle(body.a, body.b, body.c)
        return TriangleResponse(
            valid=True,
            triangle_type=triangle_type,
            message=f"Valid {triangle_type} triangle.",
        )
    except InvalidSideLengthError as e:
        return TriangleResponse(valid=False, message=str(e))
    except NotATriangleError as e:
        return TriangleResponse(valid=False, message=str(e))
