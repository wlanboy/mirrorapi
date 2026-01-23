from fastapi import APIRouter, Request, Query, Response
from typing import Optional

from header_api import process_request_logic

query_router = APIRouter(prefix="/echo", tags=["echo"])


@query_router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_query_request(
    request: Request,
    response: Response,
    statuscode: Optional[int] = Query(None, description="Sets the response status code"),
    waittime: Optional[int] = Query(None, description="Adds a delay in seconds"),
    errorcode: Optional[str] = Query(None, description="Triggers a 500 error with this message"),
):
    """
    API controlled by query parameters.

    - **statuscode**: Sets the response status code
    - **waittime**: Adds a delay in seconds
    - **errorcode**: Triggers a 500 error with this message
    """
    status_code = statuscode
    if errorcode:
        status_code = 500

    response_data, final_status = await process_request_logic(
        request=request,
        status_code=status_code,
        wait_time=waittime,
        error_message=errorcode
    )

    response.status_code = final_status
    return response_data
