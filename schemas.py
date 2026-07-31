from typing import Any

from pydantic import BaseModel


class EchoResponse(BaseModel):
    received_headers: dict[str, str]
    received_body: Any = None


class ErrorResponse(BaseModel):
    error: str


class MirrorRequest(BaseModel):
    request_data: Any


class MirrorResponse(BaseModel):
    response_data: Any
    response_status: int


class MirrorSaveRequest(BaseModel):
    request: MirrorRequest
    response: MirrorResponse


class MessageResponse(BaseModel):
    message: str


class StatusResponse(BaseModel):
    status: str
    error: str | None = None
