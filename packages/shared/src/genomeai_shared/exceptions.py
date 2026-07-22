from __future__ import annotations


class BaseError(Exception):
    def __init__(self, message: str = "", detail: str | None = None) -> None:
        self.detail = detail
        super().__init__(message)


class ConfigurationError(BaseError):
    pass


class ValidationError(BaseError):
    pass


class ApplicationError(BaseError):
    pass


class DependencyError(BaseError):
    pass
