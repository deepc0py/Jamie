"""Jamie Discord bot package."""

from .url_patterns import (
    StreamingService,
    ParsedURL,
    parse_url,
    is_supported_url,
    extract_urls,
)

__all__ = [
    "StreamingService",
    "ParsedURL",
    "parse_url",
    "is_supported_url",
    "extract_urls",
]
