
from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse

from header_api import process_request_logic

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
    status_code = None
    if statuscode is not None:
        try:
            status_code = int(statuscode)
        except ValueError:
            return JSONResponse(
                content={"error": "Invalid value for statuscode, must be an integer."},
                status_code=400
            )

    wait_time = None
    if waittime is not None:
        try:
            wait_time = int(waittime)
        except ValueError:
            return JSONResponse(
                content={"error": "Invalid value for waittime, must be an integer."},
                status_code=400
            )

    if errorcode:
        status_code = 500

    response_data, final_status = await process_request_logic(
        request=request,
        status_code=status_code,
        wait_time=wait_time,
        error_message=errorcode
    )

    response.status_code = final_status
    return response_data
