from __future__ import annotations


class SDKError(Exception):
    pass


class APIError(SDKError):
    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(message or f"API returned status {status_code}")


class ConnectionError(SDKError):
    pass


class TimeoutError(SDKError):
    pass
