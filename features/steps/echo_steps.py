import requests
from behave import then, when

BASE_URL = "http://localhost:4500"

@when('I send a POST request to "{path}" with body:')
def step_post_with_body(context, path):
    context.response = requests.post(
        f"{BASE_URL}{path}",
        json=context.text and eval(context.text)
    )

@when('I send a POST request to "{path}" with raw body:')
def step_post_with_raw_body(context, path):
    context.response = requests.post(
        f"{BASE_URL}{path}",
        data=context.text,
        headers={"Content-Type": "text/plain"}
    )

@when('I send a GET request to "{path}"')
@when('I send a GET request to "{path}" with header "{header}" = "{value}"')
def step_get(context, path, header=None, value=None):
    headers = {header: value} if header and value else {}
    context.response = requests.get(f"{BASE_URL}{path}", headers=headers)

@then("the response status code should be {status:d}")
def step_check_status_code(context, status):
    assert context.response.status_code == status, \
        f"Expected {status}, got {context.response.status_code}"

@then('the response JSON should contain "{key}" = "{value}"')
def step_check_json_value(context, key, value):
    data = context.response.json()
    parts = key.split(".")
    for p in parts:
        data = data[p]
    assert str(data) == value, f"Expected {value}, got {data}"

@then('the response header "{header}" should equal "{value}"')
def step_check_header(context, header, value):
    assert context.response.headers.get(header) == value, \
        f"Expected header {header}={value}, got {context.response.headers.get(header)}"
