from flask import Flask, request, jsonify, make_response
import time
import logging
import signal
import sys
#from waitress import serve
#from paste.translogger import TransLogger

logging.basicConfig()
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

app = Flask(__name__)

def handle_sigterm(signal, frame):
    print("SIGTERM received. Shutting down gracefully...")
    print("Cleanup complete. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

@app.route('/request', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def handle_request():
    # Default values
    status_code = 200
    wait_time = 0
    error_message = None

    request_headers = {key: value for key, value in request.headers.items()}
    
    # Process 'request-*' headers
    for header, value in request_headers.items():
        header_lower = header.lower()
        if header_lower == 'request-statuscode':
            try:
                status_code = int(value)
            except ValueError:
                return jsonify({"error": "Invalid value for request-statuscode, must be an integer."}), 400
        elif header_lower == 'request-waittime':
            try:
                wait_time = int(value)
            except ValueError:
                return jsonify({"error": "Invalid value for request-waittime, must be an integer."}), 400
        elif header_lower == 'request-errorcode':
            status_code = 500
            error_message = value
    
    # Wait for the specified time
    if wait_time > 0:
        time.sleep(wait_time)
        
    # Return an error message if specified
    if error_message:
        response_data = {"error": error_message}
        return jsonify(response_data), status_code
        
    # Get the request body
    try:
        request_body = request.json
    except Exception:
        request_body = request.get_data(as_text=True)

    # Prepare the response body, including all headers
    response_data = {
        "headers": request_headers,
        "body": request_body
    }

    # Create and return the response
    response = make_response(jsonify(response_data), status_code)
    
    excluded_headers = ['Content-Length', 'Connection', 'Host']
    for header, value in request_headers.items():
        if header not in excluded_headers:
            response.headers[header] = value

    return response

if __name__ == '__main__':
    app.run(debug=False, port=4500)
    #serve(TransLogger(app, setup_console_handler=True), host='0.0.0.0', port=4500, threads=2, expose_tracebacks=False)