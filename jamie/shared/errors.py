"""Error codes and error handling for Jamie.

This module defines the error taxonomy, exception classes, and helper utilities
for consistent error handling across the Jamie system.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCategory(str, Enum):
    """Top-level error categories for classification."""
    
    USER = "user"           # User-caused, recoverable by user action
    TRANSIENT = "transient" # Temporary, retry may help
    CONFIG = "config"       # Misconfiguration, requires admin intervention
    EXTERNAL = "external"   # Third-party service failure
    INTERNAL = "internal"   # Bug or unexpected state


class ErrorCode(str, Enum):
    """Error codes for the Jamie system.
    
    Error code format:
    - E4xxx: User errors (HTTP 4xx equivalent)
    - E5xxx: Transient errors (retry may help)
    - E6xxx: Configuration errors
    - E7xxx: External service errors
    - E8xxx: Internal/system errors
    - E9xxx: Unknown/unexpected errors
    """
    
    # User errors (4xx equivalent)
    NOT_IN_VOICE = "NOT_IN_VOICE"               # User not in a voice channel
    INVALID_URL = "INVALID_URL"                 # URL not supported/valid
    NO_SHARED_GUILD = "NO_SHARED_GUILD"         # No shared guild with user
    ALREADY_STREAMING = "ALREADY_STREAMING"     # Already streaming to this user
    NOT_REQUESTER = "NOT_REQUESTER"             # Only requester can stop
    
    # Transient errors (5xx, retry may help)
    SANDBOX_FAILED = "SANDBOX_FAILED"           # Docker sandbox failed to start
    SANDBOX_TIMEOUT = "SANDBOX_TIMEOUT"         # Sandbox operation timed out
    AGENT_TIMEOUT = "AGENT_TIMEOUT"             # Agent took too long
    AGENT_STUCK = "AGENT_STUCK"                 # Agent loop not progressing
    DISCORD_RATE_LIMIT = "DISCORD_RATE_LIMIT"   # Discord rate limited
    STREAM_DROPPED = "STREAM_DROPPED"           # Stream unexpectedly ended
    
    # Configuration errors
    DISCORD_LOGIN_FAILED = "DISCORD_LOGIN_FAILED"   # Discord login failed
    TWO_FA_REQUIRED = "TWO_FA_REQUIRED"             # Account requires 2FA
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"     # Discord credentials invalid
    NO_BOT_TOKEN = "NO_BOT_TOKEN"                   # Bot token not configured
    NO_API_KEY = "NO_API_KEY"                       # Anthropic API key missing
    
    # External service errors
    VOICE_JOIN_FAILED = "VOICE_JOIN_FAILED"         # Failed to join voice channel
    SCREEN_SHARE_FAILED = "SCREEN_SHARE_FAILED"     # Screen share didn't work
    CUA_UNAVAILABLE = "CUA_UNAVAILABLE"             # CUA service not responding
    DISCORD_DOWN = "DISCORD_DOWN"                   # Discord services unavailable
    ANTHROPIC_DOWN = "ANTHROPIC_DOWN"               # Anthropic API unavailable
    URL_UNREACHABLE = "URL_UNREACHABLE"             # Streaming URL not accessible
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"           # CAPTCHA challenge required
    
    # Internal/system errors
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"             # Cost limit hit
    MAX_ITERATIONS = "MAX_ITERATIONS"               # Max iterations exceeded
    INTERNAL = "INTERNAL"                           # Unknown internal error


# Error code metadata: (category, default_message)
_ERROR_METADATA: Dict[ErrorCode, tuple] = {
    # User errors
    ErrorCode.NOT_IN_VOICE: (
        ErrorCategory.USER,
        "User not in a voice channel"
    ),
    ErrorCode.INVALID_URL: (
        ErrorCategory.USER,
        "URL format not recognized or unsupported"
    ),
    ErrorCode.NO_SHARED_GUILD: (
        ErrorCategory.USER,
        "No shared guild found with user"
    ),
    ErrorCode.ALREADY_STREAMING: (
        ErrorCategory.USER,
        "Stream already in progress"
    ),
    ErrorCode.NOT_REQUESTER: (
        ErrorCategory.USER,
        "Only the requester can stop the stream"
    ),
    
    # Transient errors
    ErrorCode.SANDBOX_FAILED: (
        ErrorCategory.TRANSIENT,
        "Docker sandbox failed to start"
    ),
    ErrorCode.SANDBOX_TIMEOUT: (
        ErrorCategory.TRANSIENT,
        "Sandbox operation timed out"
    ),
    ErrorCode.AGENT_TIMEOUT: (
        ErrorCategory.TRANSIENT,
        "Agent took too long to respond"
    ),
    ErrorCode.AGENT_STUCK: (
        ErrorCategory.TRANSIENT,
        "Agent loop not progressing"
    ),
    ErrorCode.DISCORD_RATE_LIMIT: (
        ErrorCategory.TRANSIENT,
        "Discord rate limited the request"
    ),
    ErrorCode.STREAM_DROPPED: (
        ErrorCategory.TRANSIENT,
        "Stream unexpectedly ended"
    ),
    
    # Configuration errors
    ErrorCode.DISCORD_LOGIN_FAILED: (
        ErrorCategory.CONFIG,
        "Discord login failed"
    ),
    ErrorCode.TWO_FA_REQUIRED: (
        ErrorCategory.CONFIG,
        "Discord account requires 2FA"
    ),
    ErrorCode.INVALID_CREDENTIALS: (
        ErrorCategory.CONFIG,
        "Discord credentials are invalid"
    ),
    ErrorCode.NO_BOT_TOKEN: (
        ErrorCategory.CONFIG,
        "Bot token not configured"
    ),
    ErrorCode.NO_API_KEY: (
        ErrorCategory.CONFIG,
        "Anthropic API key not configured"
    ),
    
    # External service errors
    ErrorCode.VOICE_JOIN_FAILED: (
        ErrorCategory.EXTERNAL,
        "Failed to join voice channel"
    ),
    ErrorCode.SCREEN_SHARE_FAILED: (
        ErrorCategory.EXTERNAL,
        "Screen share failed to start"
    ),
    ErrorCode.CUA_UNAVAILABLE: (
        ErrorCategory.EXTERNAL,
        "CUA service is not responding"
    ),
    ErrorCode.DISCORD_DOWN: (
        ErrorCategory.EXTERNAL,
        "Discord services are unavailable"
    ),
    ErrorCode.ANTHROPIC_DOWN: (
        ErrorCategory.EXTERNAL,
        "Anthropic API is unavailable"
    ),
    ErrorCode.URL_UNREACHABLE: (
        ErrorCategory.EXTERNAL,
        "Streaming URL is not accessible"
    ),
    ErrorCode.CAPTCHA_REQUIRED: (
        ErrorCategory.EXTERNAL,
        "CAPTCHA challenge required"
    ),
    
    # Internal errors
    ErrorCode.BUDGET_EXCEEDED: (
        ErrorCategory.INTERNAL,
        "Cost budget exceeded for session"
    ),
    ErrorCode.MAX_ITERATIONS: (
        ErrorCategory.INTERNAL,
        "Maximum agent iterations exceeded"
    ),
    ErrorCode.INTERNAL: (
        ErrorCategory.INTERNAL,
        "An unexpected internal error occurred"
    ),
}


# User-friendly messages for Discord responses
_USER_MESSAGES: Dict[ErrorCode, str] = {
    ErrorCode.NOT_IN_VOICE: (
        "❌ You're not in any voice channel I can see.\n"
        "Join a voice channel in a server we share, then try again."
    ),
    ErrorCode.INVALID_URL: (
        "❌ I couldn't find a valid URL in your message.\n"
        "Send me a YouTube, Twitch, or Vimeo link to stream!"
    ),
    ErrorCode.NO_SHARED_GUILD: (
        "❌ We don't share any servers where I can stream.\n"
        "Invite me to your server or join one I'm already in!"
    ),
    ErrorCode.ALREADY_STREAMING: (
        "⏳ I'm already streaming somewhere else.\n"
        "DM `stop` to end that stream first."
    ),
    ErrorCode.NOT_REQUESTER: (
        "❌ Only the person who started the stream can stop it."
    ),
    ErrorCode.SANDBOX_FAILED: (
        "❌ Failed to start the streaming environment.\n"
        "Please try again in a moment."
    ),
    ErrorCode.SANDBOX_TIMEOUT: (
        "❌ Stream setup timed out.\n"
        "Please try again."
    ),
    ErrorCode.AGENT_TIMEOUT: (
        "❌ The stream took too long to set up.\n"
        "Please try again."
    ),
    ErrorCode.AGENT_STUCK: (
        "❌ Something got stuck during setup.\n"
        "Please try again."
    ),
    ErrorCode.DISCORD_RATE_LIMIT: (
        "⏳ Discord is asking me to slow down.\n"
        "Please wait a moment and try again."
    ),
    ErrorCode.STREAM_DROPPED: (
        "❌ The stream unexpectedly ended.\n"
        "Please try starting it again."
    ),
    ErrorCode.DISCORD_LOGIN_FAILED: (
        "❌ I couldn't log into Discord.\n"
        "Please contact the administrator."
    ),
    ErrorCode.TWO_FA_REQUIRED: (
        "❌ My streaming account requires 2FA setup.\n"
        "Please contact the administrator."
    ),
    ErrorCode.INVALID_CREDENTIALS: (
        "❌ My streaming credentials are invalid.\n"
        "Please contact the administrator."
    ),
    ErrorCode.VOICE_JOIN_FAILED: (
        "❌ I couldn't join the voice channel.\n"
        "Check my permissions and try again."
    ),
    ErrorCode.SCREEN_SHARE_FAILED: (
        "❌ Screen sharing failed to start.\n"
        "Please try again."
    ),
    ErrorCode.CUA_UNAVAILABLE: (
        "❌ My streaming service is currently unavailable.\n"
        "Please try again later."
    ),
    ErrorCode.DISCORD_DOWN: (
        "❌ Discord seems to be having issues.\n"
        "Please try again later."
    ),
    ErrorCode.ANTHROPIC_DOWN: (
        "❌ My AI service is currently unavailable.\n"
        "Please try again later."
    ),
    ErrorCode.URL_UNREACHABLE: (
        "❌ I couldn't load that URL.\n"
        "It might be geoblocked or require a login."
    ),
    ErrorCode.CAPTCHA_REQUIRED: (
        "❌ A CAPTCHA challenge appeared.\n"
        "Please contact the administrator."
    ),
    ErrorCode.BUDGET_EXCEEDED: (
        "❌ This session got too expensive.\n"
        "Try again with a simpler request."
    ),
    ErrorCode.MAX_ITERATIONS: (
        "❌ Setup took too many steps.\n"
        "Please try again with a different URL."
    ),
    ErrorCode.INTERNAL: (
        "❌ Something went wrong on my end.\n"
        "Please try again later."
    ),
}


# HTTP status code mapping for API responses
ERROR_HTTP_STATUS: Dict[ErrorCode, int] = {
    # User errors -> 4xx
    ErrorCode.NOT_IN_VOICE: 400,
    ErrorCode.INVALID_URL: 400,
    ErrorCode.NO_SHARED_GUILD: 400,
    ErrorCode.ALREADY_STREAMING: 409,
    ErrorCode.NOT_REQUESTER: 403,
    
    # Transient errors -> 5xx (retriable)
    ErrorCode.SANDBOX_FAILED: 503,
    ErrorCode.SANDBOX_TIMEOUT: 504,
    ErrorCode.AGENT_TIMEOUT: 504,
    ErrorCode.AGENT_STUCK: 500,
    ErrorCode.DISCORD_RATE_LIMIT: 429,
    ErrorCode.STREAM_DROPPED: 500,
    
    # Configuration errors -> 5xx (server misconfiguration)
    ErrorCode.DISCORD_LOGIN_FAILED: 401,
    ErrorCode.TWO_FA_REQUIRED: 401,
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.NO_BOT_TOKEN: 500,
    ErrorCode.NO_API_KEY: 500,
    
    # External service errors -> 5xx
    ErrorCode.VOICE_JOIN_FAILED: 502,
    ErrorCode.SCREEN_SHARE_FAILED: 500,
    ErrorCode.CUA_UNAVAILABLE: 503,
    ErrorCode.DISCORD_DOWN: 503,
    ErrorCode.ANTHROPIC_DOWN: 503,
    ErrorCode.URL_UNREACHABLE: 502,
    ErrorCode.CAPTCHA_REQUIRED: 503,
    
    # Internal errors -> 5xx
    ErrorCode.BUDGET_EXCEEDED: 402,
    ErrorCode.MAX_ITERATIONS: 500,
    ErrorCode.INTERNAL: 500,
}


class JamieError(Exception):
    """Base exception for Jamie errors.
    
    Provides structured error handling with:
    - Error code classification
    - Technical message for logging
    - User-friendly message for Discord responses
    - Additional details for debugging
    
    Example:
        raise JamieError(
            code=ErrorCode.NOT_IN_VOICE,
            message="User 123 not found in any voice channel",
            details={"user_id": 123, "guilds_checked": [456, 789]}
        )
    """
    
    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a JamieError.
        
        Args:
            code: The error code identifying the type of error.
            message: Technical message for logging. If not provided,
                uses the default message for the error code.
            user_message: User-friendly message for Discord responses.
                If not provided, uses the default user message for the error code.
            details: Additional context for debugging (e.g., IDs, states).
        """
        self.code = code
        self.message = message or self._default_message(code)
        self.user_message = user_message or self._default_user_message(code)
        self.details = details or {}
        super().__init__(self.message)
    
    @staticmethod
    def _default_message(code: ErrorCode) -> str:
        """Get the default technical message for an error code."""
        metadata = _ERROR_METADATA.get(code)
        if metadata:
            return metadata[1]
        return "An error occurred"
    
    @staticmethod
    def _default_user_message(code: ErrorCode) -> str:
        """Get the default user-friendly message for an error code."""
        return _USER_MESSAGES.get(
            code,
            "❌ Something went wrong. Please try again later."
        )
    
    @property
    def category(self) -> ErrorCategory:
        """Get the error category for this error code."""
        metadata = _ERROR_METADATA.get(self.code)
        if metadata:
            return metadata[0]
        return ErrorCategory.INTERNAL
    
    @property
    def http_status(self) -> int:
        """Get the HTTP status code for this error."""
        return ERROR_HTTP_STATUS.get(self.code, 500)
    
    def __str__(self) -> str:
        """Return a string representation for logging."""
        return f"[{self.code.value}] {self.message}"
    
    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        return (
            f"JamieError(code={self.code!r}, message={self.message!r}, "
            f"details={self.details!r})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for API responses."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "category": self.category.value,
                "details": self.details,
            }
        }


def is_user_error(code: ErrorCode) -> bool:
    """Check if an error code represents a user-caused error.
    
    User errors are recoverable by the user taking different action
    (e.g., joining a voice channel, using a different URL).
    
    Args:
        code: The error code to check.
        
    Returns:
        True if this is a user error, False otherwise.
    
    Example:
        if is_user_error(error.code):
            # Show user-friendly message without alerting admins
            await send_user_message(error.user_message)
    """
    metadata = _ERROR_METADATA.get(code)
    if metadata:
        return metadata[0] == ErrorCategory.USER
    return False


def is_retryable(code: ErrorCode) -> bool:
    """Check if an error code represents a retryable error.
    
    Retryable errors are transient failures where retrying the same
    operation may succeed (e.g., timeouts, rate limits, dropped connections).
    
    Args:
        code: The error code to check.
        
    Returns:
        True if retrying may help, False otherwise.
    
    Example:
        if is_retryable(error.code):
            await asyncio.sleep(backoff_delay)
            return await retry_operation()
    """
    metadata = _ERROR_METADATA.get(code)
    if metadata:
        return metadata[0] == ErrorCategory.TRANSIENT
    return False


def get_error_category(code: ErrorCode) -> ErrorCategory:
    """Get the category for an error code.
    
    Args:
        code: The error code to check.
        
    Returns:
        The error category, defaulting to INTERNAL if not found.
    """
    metadata = _ERROR_METADATA.get(code)
    if metadata:
        return metadata[0]
    return ErrorCategory.INTERNAL


def get_http_status(code: ErrorCode) -> int:
    """Get the HTTP status code for an error.
    
    Args:
        code: The error code to check.
        
    Returns:
        The HTTP status code, defaulting to 500 if not found.
    """
    return ERROR_HTTP_STATUS.get(code, 500)
