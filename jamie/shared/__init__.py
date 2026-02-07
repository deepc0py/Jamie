"""Shared modules for Jamie system components."""

from .errors import (
    ErrorCategory,
    ErrorCode,
    JamieError,
    ERROR_HTTP_STATUS,
    is_user_error,
    is_retryable,
    get_error_category,
    get_http_status,
)

__all__ = [
    "ErrorCategory",
    "ErrorCode",
    "JamieError",
    "ERROR_HTTP_STATUS",
    "is_user_error",
    "is_retryable",
    "get_error_category",
    "get_http_status",
]
