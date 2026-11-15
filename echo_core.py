"""Shared response-building logic for the header-, query- and path-driven
echo endpoints."""

import asyncio
import json

from fastapi import Request

from request_control import ResponseControl

# Request headers never copied onto the response: framing and encoding
# headers would describe a body the response doesn't have, hop-by-hop
# headers (RFC 9110, section 7.6.1) only apply to the incoming connection.
EXCLUDED_RESPONSE_HEADERS = {
    'connection',
    'content-encoding',
    'content-length',
    'content-type',
    'host',
    'keep-alive',
    'te',
    'trailer',
    'transfer-encoding',
    'upgrade',
}
EXCLUDED_RESPONSE_HEADER_PREFIXES = ('proxy-',)


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
    return {k: v for k, v in headers.items() if _is_forwardable(k.lower())}


def _is_forwardable(name: str) -> bool:
    return name not in EXCLUDED_RESPONSE_HEADERS and not name.startswith(EXCLUDED_RESPONSE_HEADER_PREFIXES)
