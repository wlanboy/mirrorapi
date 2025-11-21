from flask import request
from flask_smorest import Blueprint
from swagger import EchoQuerySchema, EchoResponseSchema, ErrorResponseSchema
from header_api import process_request_logic

# --- Query Parameter-based API Blueprint ---
query_blp = Blueprint(
    "query", __name__, url_prefix="/echo", description="API controlled by query parameters."
)

@query_blp.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@query_blp.arguments(EchoQuerySchema, location="query")
@query_blp.response(200, EchoResponseSchema, description="Successful request echo.")
@query_blp.response(500, ErrorResponseSchema, description="Internal Server Error triggered by parameter.")
def handle_request(query_args):
    return process_request_logic(
        status_code=query_args.get('statuscode'),
        wait_time=query_args.get('waittime'),
        error_message=query_args.get('errorcode')
    )