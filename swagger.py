from flask_swagger_ui import get_swaggerui_blueprint
from marshmallow import Schema, fields, post_load

# Schemas for API Documentation and Validation
class RequestHeadersSchema(Schema):
    statuscode = fields.Integer(load_default=None, data_key="request-statuscode", metadata={"description": "Sets the response status code."})
    waittime = fields.Integer(load_default=None, data_key="request-waittime", metadata={"description": "Adds a delay in seconds."})
    errorcode = fields.String(load_default=None, data_key="request-errorcode", metadata={"description": "Triggers a 500 error with this message."})

    @post_load
    def process_headers(self, data, **kwargs):
        if data.get("errorcode"):
            data["statuscode"] = 500
        return data

class EchoQuerySchema(Schema):
    statuscode = fields.Integer(load_default=None, metadata={"description": "Sets the response status code."})
    waittime = fields.Integer(load_default=None, metadata={"description": "Adds a delay in seconds."})
    errorcode = fields.String(load_default=None, metadata={"description": "Triggers a 500 error with this message."})

    @post_load
    def process_query_params(self, data, **kwargs):
        if data.get("errorcode"):
            data["statuscode"] = 500
        return data

class EchoResponseSchema(Schema):
    received_headers = fields.Dict(required=True)
    received_body = fields.Raw()

class ErrorResponseSchema(Schema):
    error = fields.String(required=True)

# Function to configure and register the Swagger UI
def configure_swagger_ui(app):
    """
    Configures and registers the Swagger UI blueprint on the Flask app.
    
    Args:
        app: The Flask application instance.
    """
    SWAGGER_URL = "/swagger-ui"
    API_URL = "/swagger-ui/openapi.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Mirror Echo API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)