from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from echo_core import build_echo_payload, forwardable_headers
from http_status import build_response
from request_control import (
    InvalidControlValue,
    ResponseControl,
    check_status_code,
    check_wait_time,
    parse_int,
)

echo_router = APIRouter(prefix="/echo", tags=["echo-path"])


@echo_router.api_route("/{options:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_path_request(
    request: Request,
    options: str,
    request_statuscode: str | None = Header(None, alias="request-statuscode"),
    request_waittime: str | None = Header(None, alias="request-waittime"),
    request_errorcode: str | None = Header(None, alias="request-errorcode"),
):
    """
    Echo endpoint with path-based parameters.

    Path format: `/echo/statuscode/201/waittime/2`

    Falls back to `request-*` headers if not specified in path.
    """
    try:
        control = _resolve_control(options, request_statuscode, request_waittime, request_errorcode)
    except InvalidControlValue as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    request_headers = dict(request.headers)
    response_data, final_status = await build_echo_payload(request, request_headers, control)
    return build_response(response_data, final_status, forwardable_headers(request_headers))


def _resolve_control(
    options: str,
    header_status_raw: str | None,
    header_wait_raw: str | None,
    header_error: str | None,
) -> ResponseControl:
    """Resolves status/wait/error from the path, falling back to the
    `request-*` headers when a path segment is absent."""
    path_status, path_wait, path_error = _parse_path_options(options)
    header_status = check_status_code("request-statuscode", parse_int("request-statuscode", header_status_raw))
    header_wait = check_wait_time("request-waittime", parse_int("request-waittime", header_wait_raw))

    return ResponseControl.resolve(
        path_status if path_status is not None else header_status,
        path_wait if path_wait is not None else header_wait,
        path_error if path_error is not None else header_error,
    )


def _parse_path_options(options: str) -> tuple[int | None, int | None, str | None]:
    """Parses `key/value/key/value` path segments into status/wait/error overrides."""
    status_code = wait_time = error_message = None
    parts = options.split('/')
    for i in range(0, len(parts) - 1, 2):
        key, value = parts[i].lower(), parts[i + 1]
        if key == 'statuscode':
            status_code = check_status_code('statuscode', parse_int('statuscode', value))
        elif key == 'waittime':
            wait_time = check_wait_time('waittime', parse_int('waittime', value))
        elif key == 'errorcode':
            error_message = value
    return status_code, wait_time, error_message
