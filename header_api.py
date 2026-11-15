from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from echo_core import build_echo_payload
from http_status import build_response
from request_control import InvalidControlValue, ResponseControl

header_router = APIRouter(prefix="/request", tags=["request"])


@header_router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_header_request(
    request: Request,
    request_statuscode: str | None = Header(None, alias="request-statuscode"),
    request_waittime: str | None = Header(None, alias="request-waittime"),
    request_errorcode: str | None = Header(None, alias="request-errorcode"),
):
    """
    API controlled by headers.

    - **request-statuscode**: Sets the response status code
    - **request-waittime**: Adds a delay in seconds
    - **request-errorcode**: Triggers a 500 error with this message
    """
    try:
        control = ResponseControl.parse(
            status_field="request-statuscode", status_raw=request_statuscode,
            wait_field="request-waittime", wait_raw=request_waittime,
            error_message=request_errorcode,
        )
    except InvalidControlValue as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    response_data, final_status = await build_echo_payload(request, dict(request.headers), control)
    return build_response(response_data, final_status)
