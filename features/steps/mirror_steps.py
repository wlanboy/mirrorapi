import requests
import json
from behave import when

BASE_URL = "http://localhost:4500"

@when('I send a {method} request to "{path}" with body:')
def step_impl(context, method, path):
    try:
        body = json.loads(context.text)
    except Exception:
        body = context.text

    method = method.upper()
    if method == "GET":
        context.response = requests.get(f"{BASE_URL}{path}", json=body)
    elif method == "POST":
        context.response = requests.post(f"{BASE_URL}{path}", json=body)
    elif method == "PUT":
        context.response = requests.put(f"{BASE_URL}{path}", json=body)
    elif method == "DELETE":
        context.response = requests.delete(f"{BASE_URL}{path}", json=body)
    elif method == "PATCH":
        context.response = requests.patch(f"{BASE_URL}{path}", json=body)
    else:
        raise ValueError(f"Unsupported method {method}")
