from flask import request
from flask_smorest import Blueprint
from swagger import RequestHeadersSchema, EchoResponseSchema, ErrorResponseSchema
import time

# Create a shared function for the core logic
def process_request_logic(status_code=None, wait_time=None, error_message=None):
    """
    Unified function to process the request based on parameters from headers or path.
    """
    request_headers = {key: value for key, value in request.headers.items()}
    
    if wait_time is not None:
        time.sleep(wait_time)
        
    if error_message is not None:
        return {"error": error_message}, 500
        
    try:
        request_body = request.get_json(silent=True)
    except Exception:
        request_body = request.get_data(as_text=True)

    response_data = {
        "received_headers": request_headers,
        "received_body": request_body
    }
    
    return response_data, status_code if status_code is not None else 200

# --- Header-based API Blueprint ---
header_blp = Blueprint(
    "request", __name__, url_prefix="/request", description="API controlled by headers."
)

@header_blp.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@header_blp.arguments(RequestHeadersSchema, location="headers")
@header_blp.response(200, EchoResponseSchema, description="Successful request echo.")
@header_blp.response(500, ErrorResponseSchema, description="Internal Server Error triggered by header.")
def handle_header_request(headers_args):
    # Process request using the data validated and parsed by Marshmallow
    return process_request_logic(
        status_code=headers_args.get('statuscode'),
        wait_time=headers_args.get('waittime'),
        error_message=headers_args.get('errorcode')
    )