import requests
import json
import time

# Base URL of the running Flask API
API_URL = "http://127.0.0.1:4500/request"

def run_test(scenario_name, method="GET", headers=None, data=None):
    print("=" * 50)
    print(f"Testing Scenario: {scenario_name}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        if method.upper() in ["POST", "PUT", "PATCH"]:
            response = requests.request(method, API_URL, headers=headers, json=data)
        else:
            response = requests.request(method, API_URL, headers=headers)
            
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n--- Request Details ---")
        print(f"Method: {method}")
        print(f"URL: {API_URL}")
        print(f"Headers: {headers}")
        if data:
            print(f"Body: {json.dumps(data, indent=2)}")
        
        print("\n--- Response Details ---")
        print(f"Status Code: {response.status_code}")
        print(f"Time Taken: {duration:.2f} seconds")
        print(f"Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print("\nResponse Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        
    print("\n\n")


if __name__ == "__main__":
    # Ensure your Flask API (main.py) is running before executing this script.
    
    # 1. Standard Request (Default behavior)
    run_test(
        "Default behavior (POST, returns headers and body)",
        method="POST",
        headers={"Content-Type": "application/json"},
        data={"message": "Hello from test script!", "user_id": 123}
    )
    
    # 2. Scenario A: Set a specific HTTP status code (e.g., 201 Created)
    run_test(
        "Scenario A: Setting Status Code to 201",
        method="GET",
        headers={"request-statuscode": "201"}
    )
    
    # 3. Scenario B: Wait for a specified time (e.g., 3 seconds)
    run_test(
        "Scenario B: Adding a 3-second wait time",
        method="GET",
        headers={"request-waittime": "3"}
    )
    
    # 4. Scenario C: Return a 500 Internal Server Error with a custom message
    run_test(
        "Scenario C: Triggering a 500 error with a custom message",
        method="POST",
        headers={"request-errorcode": "Service is currently unavailable"},
        data={"operation": "critical_task"}
    )