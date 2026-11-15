from typing import Any

from pydantic import BaseModel, Field

from http_status import MAX_STATUS_CODE, MIN_STATUS_CODE


class EchoResponse(BaseModel):
    received_headers: dict[str, str]
    received_body: Any = None


class ErrorResponse(BaseModel):
    error: str


class MirrorRequest(BaseModel):
    request_data: Any
    method: str | None = None
    query_params: dict[str, str] | None = None
    ttl_seconds: int | None = None


class MirrorResponse(BaseModel):
    response_data: Any
    response_status: int = Field(ge=MIN_STATUS_CODE, le=MAX_STATUS_CODE)


class MirrorSaveRequest(BaseModel):
    request: MirrorRequest
    response: MirrorResponse


class MessageResponse(BaseModel):
    message: str


class StatusResponse(BaseModel):
    status: str
    error: str | None = None
