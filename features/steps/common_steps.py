# features/steps/common_steps.py
from behave import given

BASE_URL = "http://localhost:4501"

@given("the API is running")
def step_impl(context):
    pass
