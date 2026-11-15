"""HTTP status-code limits and the response type each status allows."""

from typing import Any

from fastapi import Response
from fastapi.responses import JSONResponse

# 1xx is left out on purpose: an informational status can't be the final
# response. h11 aborts the connection, httptools sends it and the client hangs.
MIN_STATUS_CODE = 200
MAX_STATUS_CODE = 599

# Statuses that must not carry a body (RFC 9110, sections 15.3.5 and 15.4.5).
NO_BODY_STATUS_CODES = {204, 304}


def is_valid_status(status_code: int) -> bool:
    return MIN_STATUS_CODE <= status_code <= MAX_STATUS_CODE


def build_response(content: Any, status_code: int, headers: dict[str, str] | None = None) -> Response:
    """JSON response, or an empty one for 204 and 304."""
    if status_code in NO_BODY_STATUS_CODES:
        return Response(status_code=status_code, headers=headers)
    return JSONResponse(content=content, status_code=status_code, headers=headers)
