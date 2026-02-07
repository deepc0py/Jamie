"""Request/response validation utilities."""

from typing import Optional, List
from urllib.parse import urlparse
import re

from jamie.shared.errors import JamieError, ErrorCode
from jamie.shared.models import StreamRequest


class ValidationError(JamieError):
    """Validation error."""
    pass


def validate_url(url: str) -> bool:
    """Validate that a URL is well-formed and uses http/https."""
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def validate_discord_id(id_str: str) -> bool:
    """Validate Discord snowflake ID format."""
    if not id_str:
        return False
    try:
        id_int = int(id_str)
        # Discord IDs are 17-19 digits
        return 10**16 <= id_int < 10**20
    except ValueError:
        return False


def validate_stream_request(request: StreamRequest) -> List[str]:
    """
    Validate a stream request and return list of errors.
    Returns empty list if valid.
    """
    errors = []
    
    if not validate_url(str(request.url)):
        errors.append("Invalid URL format")
    
    if not validate_discord_id(request.guild_id):
        errors.append("Invalid guild_id format")
    
    if not validate_discord_id(request.channel_id):
        errors.append("Invalid channel_id format")
    
    if not validate_discord_id(request.requester_id):
        errors.append("Invalid requester_id format")
    
    if not request.channel_name or len(request.channel_name) > 100:
        errors.append("Invalid channel_name")
    
    if request.webhook_url and not validate_url(str(request.webhook_url)):
        errors.append("Invalid webhook_url format")
    
    return errors


def require_valid_stream_request(request: StreamRequest) -> None:
    """Validate stream request or raise ValidationError."""
    errors = validate_stream_request(request)
    if errors:
        raise ValidationError(
            ErrorCode.INVALID_URL,
            f"Validation failed: {', '.join(errors)}",
            user_message="Invalid request. Please check your input."
        )
