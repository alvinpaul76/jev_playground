from typing import Any

from pydantic import BaseModel

PROBLEM_JSON = "application/problem+json"


class Problem(BaseModel):
    """RFC 9457 problem details, plus a stable machine-readable `code`."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    code: str
    request_id: str | None = None


def problem_response(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {PROBLEM_JSON: {"schema": Problem.model_json_schema()}},
    }
