import asyncio

from fastapi import APIRouter, Header, Request, Response

header_router = APIRouter(prefix="/request", tags=["request"])


async def process_request_logic(
    request: Request,
    status_code: int | None = None,
    wait_time: int | None = None,
    error_message: str | None = None
) -> tuple[dict, int]:
    """
    Unified function to process the request based on parameters from headers or path.
    """
    request_headers = dict(request.headers)

    if wait_time is not None and wait_time > 0:
        await asyncio.sleep(wait_time)

    if error_message is not None:
        return {"error": error_message}, 500

    try:
        request_body = await request.json()
    except Exception:
        request_body = (await request.body()).decode("utf-8") or None

    response_data = {
        "received_headers": request_headers,
        "received_body": request_body
    }

    return response_data, status_code if status_code is not None else 200


@header_router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_header_request(
    request: Request,
    response: Response,
    request_statuscode: int | None = Header(None, alias="request-statuscode"),
    request_waittime: int | None = Header(None, alias="request-waittime"),
    request_errorcode: str | None = Header(None, alias="request-errorcode"),
):
    """
    API controlled by headers.

    - **request-statuscode**: Sets the response status code
    - **request-waittime**: Adds a delay in seconds
    - **request-errorcode**: Triggers a 500 error with this message
    """
    status_code = request_statuscode
    if request_errorcode:
        status_code = 500

    response_data, final_status = await process_request_logic(
        request=request,
        status_code=status_code,
        wait_time=request_waittime,
        error_message=request_errorcode
    )

    response.status_code = final_status
    return response_data
