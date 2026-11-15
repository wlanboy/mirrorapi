"""Status-code/wait-time/error-message control values shared by every
echo-style endpoint (header-, query- and path-driven)."""

import os
from dataclasses import dataclass

from http_status import MAX_STATUS_CODE, MIN_STATUS_CODE, is_valid_status

# Upper bound for the requested delay, so a single request can't hold a
# connection (and a worker slot) open indefinitely.
MAX_WAIT_SECONDS = int(os.environ.get("MAX_WAIT_SECONDS", "300"))


class InvalidControlValue(ValueError):
    """Raised when a status-code/wait-time control value is invalid."""

    def __init__(self, field: str, reason: str = "must be an integer"):
        self.field = field
        super().__init__(f"Invalid value for {field}, {reason}.")


def parse_int(field: str, raw: str | None) -> int | None:
    """Parses a raw control value, or raises InvalidControlValue if it isn't one."""
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        raise InvalidControlValue(field) from None


def check_status_code(field: str, status_code: int | None) -> int | None:
    if status_code is not None and not is_valid_status(status_code):
        raise InvalidControlValue(field, f"must be between {MIN_STATUS_CODE} and {MAX_STATUS_CODE}")
    return status_code


def check_wait_time(field: str, wait_time: int | None) -> int | None:
    if wait_time is not None and not 0 <= wait_time <= MAX_WAIT_SECONDS:
        raise InvalidControlValue(field, f"must be between 0 and {MAX_WAIT_SECONDS}")
    return wait_time


@dataclass(frozen=True)
class ResponseControl:
    """Bundles the status-code/wait-time/error-message clump into one value."""

    status_code: int = 200
    wait_time: int = 0
    error_message: str | None = None

    @classmethod
    def resolve(
        cls,
        status_code: int | None,
        wait_time: int | None,
        error_message: str | None,
    ) -> ResponseControl:
        """Applies defaults, forcing a 500 on error (the shared rule for every
        echo-style endpoint). Values must already be range-checked."""
        return cls(
            status_code=500 if error_message else (status_code if status_code is not None else 200),
            wait_time=wait_time or 0,
            error_message=error_message,
        )

    @classmethod
    def parse(
        cls,
        *,
        status_field: str,
        status_raw: str | None,
        wait_field: str,
        wait_raw: str | None,
        error_message: str | None,
    ) -> ResponseControl:
        """Parses and range-checks raw status-code/wait-time strings."""
        return cls.resolve(
            check_status_code(status_field, parse_int(status_field, status_raw)),
            check_wait_time(wait_field, parse_int(wait_field, wait_raw)),
            error_message,
        )
