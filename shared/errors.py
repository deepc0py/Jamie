"""
Error codes and exception classes for Jamie.

This module defines the standardized error codes used across
the Jamie system and corresponding exception classes.

Error Codes:
    ERR_BUSY: Another stream is active
    ERR_INVALID_URL: URL not parseable or blocked
    ERR_SANDBOX_FAILED: Docker sandbox won't start
    ERR_LOGIN_FAILED: Discord login failed
    ERR_2FA_REQUIRED: Account requires 2FA
    ERR_CAPTCHA: CAPTCHA required
    ERR_CHANNEL_NOT_FOUND: Voice channel not accessible
    ERR_SHARE_FAILED: Screen share didn't work
    ERR_TIMEOUT: Operation timed out
    ERR_BUDGET_EXCEEDED: API cost limit reached
    ERR_MAX_ITERATIONS: Agent loop exceeded limit
    ERR_UNKNOWN: Unexpected error

Classes:
    JamieError: Base exception for all Jamie errors
    StreamError: Error during streaming operations
    AuthError: Authentication-related errors
    SandboxError: Docker sandbox errors
"""

from typing import Optional


class ErrorCode:
    """Standardized error codes for the Jamie system."""
    
    # Session errors
    BUSY = "ERR_BUSY"
    INVALID_URL = "ERR_INVALID_URL"
    
    # Sandbox errors
    SANDBOX_FAILED = "ERR_SANDBOX_FAILED"
    
    # Authentication errors
    LOGIN_FAILED = "ERR_LOGIN_FAILED"
    TWO_FA_REQUIRED = "ERR_2FA_REQUIRED"
    CAPTCHA = "ERR_CAPTCHA"
    
    # Discord errors
    CHANNEL_NOT_FOUND = "ERR_CHANNEL_NOT_FOUND"
    SHARE_FAILED = "ERR_SHARE_FAILED"
    
    # Agent errors
    TIMEOUT = "ERR_TIMEOUT"
    BUDGET_EXCEEDED = "ERR_BUDGET_EXCEEDED"
    MAX_ITERATIONS = "ERR_MAX_ITERATIONS"
    
    # Generic
    UNKNOWN = "ERR_UNKNOWN"


class JamieError(Exception):
    """
    Base exception for all Jamie errors.
    
    Attributes:
        message: Human-readable error description
        code: Standardized error code from ErrorCode
        details: Optional additional context
    """
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.UNKNOWN,
        details: Optional[str] = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details


class StreamError(JamieError):
    """Error during streaming operations."""
    pass


class AuthError(JamieError):
    """Authentication-related errors (login, 2FA, captcha)."""
    pass


class SandboxError(JamieError):
    """Docker sandbox errors."""
    pass
