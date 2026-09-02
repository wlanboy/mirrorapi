from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from echo_core import build_echo_payload, forwardable_headers
from request_control import InvalidControlValue, ResponseControl, parse_int

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
    return JSONResponse(
        content=response_data,
        status_code=final_status,
        headers=forwardable_headers(request_headers),
    )


def _resolve_control(
    options: str,
    header_status_raw: str | None,
    header_wait_raw: str | None,
    header_error: str | None,
) -> ResponseControl:
    """Resolves status/wait/error from the path, falling back to the
    `request-*` headers when a path segment is absent."""
    path_status, path_wait, path_error = _parse_path_options(options)
    header_status = parse_int("request-statuscode", header_status_raw)
    header_wait = parse_int("request-waittime", header_wait_raw)

    status_code = path_status if path_status is not None else header_status
    wait_time = path_wait if path_wait is not None else header_wait
    error_message = path_error if path_error is not None else header_error

    return ResponseControl(
        status_code=500 if error_message else (status_code if status_code is not None else 200),
        wait_time=wait_time or 0,
        error_message=error_message,
    )


def _parse_path_options(options: str) -> tuple[int | None, int | None, str | None]:
    """Parses `key/value/key/value` path segments into status/wait/error overrides."""
    status_code = wait_time = error_message = None
    parts = options.split('/')
    for i in range(0, len(parts) - 1, 2):
        key, value = parts[i].lower(), parts[i + 1]
        if key == 'statuscode':
            status_code = parse_int('statuscode', value)
        elif key == 'waittime':
            wait_time = parse_int('waittime', value)
        elif key == 'errorcode':
            error_message = value
    return status_code, wait_time, error_message
