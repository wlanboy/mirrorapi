from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse

from echo_core import build_echo_payload
from request_control import InvalidControlValue, ResponseControl

query_router = APIRouter(prefix="/echo", tags=["echo"])


@query_router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_query_request(
    request: Request,
    response: Response,
    statuscode: str | None = Query(None, description="Sets the response status code"),
    waittime: str | None = Query(None, description="Adds a delay in seconds"),
    errorcode: str | None = Query(None, description="Triggers a 500 error with this message"),
):
    """
    API controlled by query parameters.

    - **statuscode**: Sets the response status code
    - **waittime**: Adds a delay in seconds
    - **errorcode**: Triggers a 500 error with this message
    """
    try:
        control = ResponseControl.parse(
            status_field="statuscode", status_raw=statuscode,
            wait_field="waittime", wait_raw=waittime,
            error_message=errorcode,
        )
    except InvalidControlValue as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

    response_data, final_status = await build_echo_payload(request, dict(request.headers), control)
    response.status_code = final_status
    return response_data
