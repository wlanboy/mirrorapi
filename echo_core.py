"""Shared response-building logic for the header-, query- and path-driven
echo endpoints."""

import asyncio
import json

from fastapi import Request

from request_control import ResponseControl

EXCLUDED_RESPONSE_HEADERS = {'content-length', 'connection', 'host', 'content-type'}


async def build_echo_payload(
    request: Request,
    request_headers: dict[str, str],
    control: ResponseControl,
) -> tuple[dict, int]:
    """Waits if requested, then builds the echoed response body (or the error body)."""
    if control.wait_time > 0:
        await asyncio.sleep(control.wait_time)

    if control.error_message:
        return {"error": control.error_message}, control.status_code

    return {
        "received_headers": request_headers,
        "received_body": await _read_body(request),
    }, control.status_code


async def _read_body(request: Request):
    try:
        return await request.json()
    except json.JSONDecodeError:
        body_bytes = await request.body()
        return body_bytes.decode("utf-8") if body_bytes else None


def forwardable_headers(headers: dict[str, str]) -> dict[str, str]:
    """Request headers safe to copy onto the response (path-echo endpoint only)."""
    return {k: v for k, v in headers.items() if k.lower() not in EXCLUDED_RESPONSE_HEADERS}
