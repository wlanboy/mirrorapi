from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
import asyncio

echo_router = APIRouter(prefix="/echo", tags=["echo-path"])


@echo_router.api_route("/{options:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_path_request(
    request: Request,
    options: str,
    request_statuscode: Optional[str] = Header(None, alias="request-statuscode"),
    request_waittime: Optional[str] = Header(None, alias="request-waittime"),
    request_errorcode: Optional[str] = Header(None, alias="request-errorcode"),
):
    """
    Echo endpoint with path-based parameters.

    Path format: `/echo/statuscode/201/waittime/2`

    Falls back to `request-*` headers if not specified in path.
    """
    # Parse and validate header values
    header_statuscode = None
    header_waittime = None

    if request_statuscode is not None:
        try:
            header_statuscode = int(request_statuscode)
        except (ValueError, TypeError):
            return JSONResponse(
                content={"error": "Invalid value for request-statuscode, must be an integer."},
                status_code=400
            )

    if request_waittime is not None:
        try:
            header_waittime = int(request_waittime)
        except (ValueError, TypeError):
            return JSONResponse(
                content={"error": "Invalid value for request-waittime, must be an integer."},
                status_code=400
            )

    path_params = {}
    parts = options.split('/')
    for i in range(0, len(parts), 2):
        key = parts[i].lower()
        if i + 1 < len(parts):
            value = parts[i + 1]
            if key == 'statuscode':
                try:
                    path_params['status_code'] = int(value)
                except ValueError:
                    return JSONResponse(
                        content={"error": "Invalid value for statuscode, must be an integer."},
                        status_code=400
                    )
            elif key == 'waittime':
                try:
                    path_params['wait_time'] = int(value)
                except ValueError:
                    return JSONResponse(
                        content={"error": "Invalid value for waittime, must be an integer."},
                        status_code=400
                    )
            elif key == 'errorcode':
                path_params['error_message'] = value
                path_params['status_code'] = 500

    return await process_path_request_logic(
        request,
        path_params.get('status_code'),
        path_params.get('wait_time'),
        path_params.get('error_message'),
        header_statuscode,
        header_waittime,
        request_errorcode
    )


async def process_path_request_logic(
    request: Request,
    status_code: Optional[int] = None,
    wait_time: Optional[int] = None,
    error_message: Optional[str] = None,
    header_statuscode: Optional[int] = None,
    header_waittime: Optional[int] = None,
    header_errorcode: Optional[str] = None
):
    """Process request with path parameters, falling back to headers."""
    request_headers = dict(request.headers)

    # Use header values as fallback if path params not provided
    if status_code is None and header_statuscode is not None:
        status_code = header_statuscode
    if wait_time is None and header_waittime is not None:
        wait_time = header_waittime
    if error_message is None and header_errorcode is not None:
        status_code = 500
        error_message = header_errorcode

    # Set defaults
    if status_code is None:
        status_code = 200
    if wait_time is None:
        wait_time = 0

    # Wait for the specified time
    if wait_time > 0:
        await asyncio.sleep(wait_time)

    # Return an error message if specified
    if error_message:
        return JSONResponse(
            content={"error": error_message},
            status_code=status_code,
            headers={k: v for k, v in request_headers.items()
                     if k.lower() not in ['content-length', 'connection', 'host']}
        )

    # Get the request body
    try:
        request_body = await request.json()
    except Exception:
        body_bytes = await request.body()
        request_body = body_bytes.decode("utf-8") if body_bytes else None

    # Prepare the response
    response_data = {
        "received_headers": request_headers,
        "received_body": request_body
    }

    # Create response with copied headers
    excluded_headers = ['content-length', 'connection', 'host']
    response_headers = {k: v for k, v in request_headers.items()
                        if k.lower() not in excluded_headers}

    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=response_headers
    )
