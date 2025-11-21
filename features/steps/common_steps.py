# features/steps/common_steps.py
import requests
from behave import given, when, then
import json

BASE_URL = "http://localhost:4501"

@given("the API is running")
def step_impl(context):
    pass
