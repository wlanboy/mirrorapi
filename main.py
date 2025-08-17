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

def process_request_logic(status_code=None, wait_time=None, error_message=None):
    # Get all request headers
    request_headers = {key: value for key, value in request.headers.items()}
    
    # Process 'request-*' headers as secondary source, if not provided by path
    for header, value in request_headers.items():
        header_lower = header.lower()
        if header_lower == 'request-statuscode' and status_code is None:
            try:
                status_code = int(value)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid value for request-statuscode, must be an integer."}), 400
        elif header_lower == 'request-waittime' and wait_time is None:
            try:
                wait_time = int(value)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid value for request-waittime, must be an integer."}), 400
        elif header_lower == 'request-errorcode' and error_message is None:
            status_code = 500
            error_message = value

    # Set defaults if no parameters were provided from headers or path
    if status_code is None: status_code = 200
    if wait_time is None: wait_time = 0

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
        "received_headers": request_headers,
        "received_body": request_body
    }

    # Create and return the response
    response = make_response(jsonify(response_data), status_code)
    
    # Copy all request headers to the response headers
    excluded_headers = ['Content-Length', 'Connection', 'Host']
    for header, value in request_headers.items():
        if header not in excluded_headers:
            response.headers[header] = value

    return response

# --- Header-based API Endpoint ---
@app.route('/request', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def handle_header_request():
    return process_request_logic()

# --- Path-based Echo Endpoint ---
@app.route('/echo/<path:options>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def handle_path_request(options):
    path_params = {}
    parts = options.split('/')
    
    for i in range(0, len(parts), 2):
        key = parts[i].lower()
        if i + 1 < len(parts):
            value = parts[i+1]
            if key == 'statuscode':
                path_params['status_code'] = int(value)
            elif key == 'waittime':
                path_params['wait_time'] = int(value)
            elif key == 'errorcode':
                path_params['error_message'] = value

    return process_request_logic(**path_params)

if __name__ == '__main__':
    app.run(debug=False, port=4500)
    #serve(TransLogger(app, setup_console_handler=True), host='0.0.0.0', port=4500, threads=2, expose_tracebacks=False)