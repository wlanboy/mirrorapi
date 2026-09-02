"""Status-code/wait-time/error-message control values shared by every
echo-style endpoint (header-, query- and path-driven)."""

from dataclasses import dataclass


class InvalidControlValue(ValueError):
    """Raised when a status-code/wait-time control value isn't a valid integer."""

    def __init__(self, field: str):
        self.field = field
        super().__init__(f"Invalid value for {field}, must be an integer.")


def parse_int(field: str, raw: str | None) -> int | None:
    """Parses a raw control value, or raises InvalidControlValue if it isn't one."""
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        raise InvalidControlValue(field) from None


@dataclass(frozen=True)
class ResponseControl:
    """Bundles the status-code/wait-time/error-message clump into one value."""

    status_code: int = 200
    wait_time: int = 0
    error_message: str | None = None

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
        """Parses raw status-code/wait-time strings, forcing a 500 on error
        (the shared rule for every echo-style endpoint)."""
        status_code = parse_int(status_field, status_raw)
        wait_time = parse_int(wait_field, wait_raw)
        return cls(
            status_code=500 if error_message else (status_code if status_code is not None else 200),
            wait_time=wait_time or 0,
            error_message=error_message,
        )
