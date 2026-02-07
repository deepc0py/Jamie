"""Jamie Discord bot package."""

from .bot import JamieBot, create_bot
from .cua_client import CUAClient, CUAClientConfig, CUAClientError
from .url_patterns import (
    StreamingService,
    ParsedURL,
    parse_url,
    is_supported_url,
    extract_urls,
)
from .webhook import WebhookReceiver, StatusCallback

__all__ = [
    "JamieBot",
    "create_bot",
    "CUAClient",
    "CUAClientConfig",
    "CUAClientError",
    "StreamingService",
    "ParsedURL",
    "parse_url",
    "is_supported_url",
    "extract_urls",
    "WebhookReceiver",
    "StatusCallback",
]
