import requests
import json
import time
import sys

# Base URLs of the running Flask API
API_URL_HEADERS = "http://127.0.0.1:4500/request"
API_URL_PATH = "http://127.0.0.1:4500/echo"

def run_test(scenario_name, url, method="GET", headers=None, data=None, 
             expected_status_code=200, expected_waittime=0, expected_error_message=None):
    """
    Sends a test request, prints details, and validates the response.
    """
    print("=" * 50)
    print(f"Testing Scenario: {scenario_name}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        if method.upper() in ["POST", "PUT", "PATCH"]:
            response = requests.request(method, url, headers=headers, json=data)
        else:
            response = requests.request(method, url, headers=headers)
            
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n--- Response Details ---")
        print(f"Status Code: {response.status_code}")
        print(f"Time Taken: {duration:.2f} seconds")
        print(f"Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print("\nResponse Body:")
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            response_data = response.text
            print(response_data)

        # --- VALIDATION ---
        print("\n--- Validation ---")
        
        # 1. Validate Status Code
        if response.status_code == expected_status_code:
            print(f"✓ Status Code Test PASSED: Expected {expected_status_code}, got {response.status_code}")
        else:
            print(f"✗ Status Code Test FAILED: Expected {expected_status_code}, got {response.status_code}")
            sys.exit(1)

        # 2. Validate Wait Time (with a tolerance)
        if expected_waittime > 0:
            if expected_waittime <= duration < expected_waittime + 1:
                print(f"✓ Wait Time Test PASSED: Expected ~{expected_waittime}s, got {duration:.2f}s")
            else:
                print(f"✗ Wait Time Test FAILED: Expected ~{expected_waittime}s, got {duration:.2f}s")
                sys.exit(1)

        # 3. Validate Error Message
        if expected_error_message:
            if isinstance(response_data, dict) and response_data.get('error') == expected_error_message:
                print(f"✓ Error Message Test PASSED: Expected '{expected_error_message}', got '{response_data.get('error')}'")
            else:
                print(f"✗ Error Message Test FAILED: Expected '{expected_error_message}', got '{response_data}'")
                sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
        
    print("\n\n")


if __name__ == "__main__":
    # Ensure your Flask API (main.py) is running before executing this script.
    
    # --- Header-based API Tests (/request) ---
    print("--- Running Header-based API Tests ---")
    
    # 1. Standard Request (Default behavior)
    run_test(
        "Default behavior (POST)",
        API_URL_HEADERS,
        method="POST",
        headers={"Content-Type": "application/json"},
        data={"message": "Hello from test script!"}
    )
    
    # 2. Scenario A: Set status code
    run_test(
        "Scenario A: Setting Status Code to 201",
        API_URL_HEADERS,
        method="GET",
        headers={"request-statuscode": "201"},
        expected_status_code=201
    )
    
    # 3. Scenario B: Add a wait time
    run_test(
        "Scenario B: Adding a 3-second wait time",
        API_URL_HEADERS,
        method="GET",
        headers={"request-waittime": "3"},
        expected_waittime=3
    )
    
    # 4. Scenario C: Trigger an error
    run_test(
        "Scenario C: Triggering a 500 error",
        API_URL_HEADERS,
        method="POST",
        headers={"request-errorcode": "Invalid data provided"},
        data={"operation": "critical_task"},
        expected_status_code=500,
        expected_error_message="Invalid data provided"
    )
    
    # --- Path-based API Tests (/api/echo) ---
    print("--- Running Path-based API Tests ---")
    
    # 5. Path Test: Set Status Code
    run_test(
        "Path Test: Setting Status Code to 202 via path",
        f"{API_URL_PATH}/statuscode/202",
        method="GET",
        expected_status_code=202
    )

    # 6. Path Test: Set Wait Time
    run_test(
        "Path Test: Adding a 2-second wait time via path",
        f"{API_URL_PATH}/waittime/2",
        method="GET",
        expected_waittime=2
    )
    
    # 7. Path Test: Trigger Error
    run_test(
        "Path Test: Triggering a 500 error via path",
        f"{API_URL_PATH}/statuscode/500/errorcode/Path-based-error",
        method="GET",
        expected_status_code=500,
        expected_error_message="Path-based-error"
    )
    
    # 8. Path Test: Combined parameters
    run_test(
        "Path Test: Combined Status Code and Wait Time",
        f"{API_URL_PATH}/statuscode/204/waittime/2",
        method="GET",
        expected_status_code=204,
        expected_waittime=2
    )