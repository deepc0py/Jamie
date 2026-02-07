"""URL pattern matching for supported streaming services."""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class StreamingService(str, Enum):
    """Supported streaming services."""
    YOUTUBE = "youtube"
    TWITCH = "twitch"
    VIMEO = "vimeo"
    WIKIPEDIA = "wikipedia"
    GENERIC = "generic"  # Any other URL


@dataclass
class ParsedURL:
    """Parsed URL with service identification."""
    original: str
    service: StreamingService
    video_id: Optional[str] = None
    normalized: Optional[str] = None


# URL patterns for each service
# Each pattern has a capture group for the video/content ID
PATTERNS: dict[StreamingService, list[re.Pattern[str]]] = {
    StreamingService.YOUTUBE: [
        # Standard watch URL: youtube.com/watch?v=VIDEO_ID
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'),
        # Short URL: youtu.be/VIDEO_ID
        re.compile(r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})'),
        # Embed URL: youtube.com/embed/VIDEO_ID
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})'),
        # Shorts URL: youtube.com/shorts/VIDEO_ID
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})'),
        # Live URL: youtube.com/live/VIDEO_ID
        re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})'),
    ],
    StreamingService.TWITCH: [
        # Channel URL: twitch.tv/CHANNEL_NAME
        re.compile(r'(?:https?://)?(?:www\.)?twitch\.tv/([a-zA-Z0-9_]+)(?:/.*)?'),
    ],
    StreamingService.VIMEO: [
        # Standard Vimeo URL: vimeo.com/VIDEO_ID
        re.compile(r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)'),
        # Player embed: player.vimeo.com/video/VIDEO_ID
        re.compile(r'(?:https?://)?player\.vimeo\.com/video/(\d+)'),
    ],
    StreamingService.WIKIPEDIA: [
        # Wikipedia article: en.wikipedia.org/wiki/ARTICLE
        re.compile(r'(?:https?://)?(?:([a-z]{2})\.)?wikipedia\.org/wiki/([^\s?#]+)'),
    ],
}

# General URL pattern for extracting any URL from text
URL_EXTRACT_PATTERN = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+'
)

# Pattern for validating a generic URL
GENERIC_URL_PATTERN = re.compile(
    r'^https?://[^\s<>"{}|\\^`\[\]]+$'
)


def parse_url(url: str) -> Optional[ParsedURL]:
    """
    Parse and validate a URL, identifying the streaming service.
    
    Args:
        url: The URL string to parse
        
    Returns:
        ParsedURL object if valid, None if not a valid URL
    """
    url = url.strip()
    
    # Try each service pattern
    for service, patterns in PATTERNS.items():
        for pattern in patterns:
            match = pattern.match(url)
            if match:
                groups = match.groups()
                
                # Handle Wikipedia specially (has language code and article name)
                if service == StreamingService.WIKIPEDIA:
                    lang = groups[0] or "en"
                    article = groups[1] if len(groups) > 1 else groups[0]
                    video_id = article
                    normalized = f"https://{lang}.wikipedia.org/wiki/{article}"
                # Handle other services
                elif groups:
                    video_id = groups[0]
                    normalized = _normalize_url(service, video_id)
                else:
                    video_id = None
                    normalized = url
                
                return ParsedURL(
                    original=url,
                    service=service,
                    video_id=video_id,
                    normalized=normalized
                )
    
    # Check if it's a valid generic URL
    if GENERIC_URL_PATTERN.match(url):
        return ParsedURL(
            original=url,
            service=StreamingService.GENERIC,
            video_id=None,
            normalized=url
        )
    
    return None


def _normalize_url(service: StreamingService, video_id: str) -> str:
    """Generate normalized URL for a service."""
    if service == StreamingService.YOUTUBE:
        return f"https://www.youtube.com/watch?v={video_id}"
    elif service == StreamingService.TWITCH:
        return f"https://www.twitch.tv/{video_id}"
    elif service == StreamingService.VIMEO:
        return f"https://vimeo.com/{video_id}"
    else:
        return video_id


def is_supported_url(url: str) -> bool:
    """
    Check if URL is from a supported service (not just generic).
    
    Args:
        url: The URL string to check
        
    Returns:
        True if URL is from YouTube, Twitch, Vimeo, or Wikipedia
    """
    parsed = parse_url(url)
    if parsed is None:
        return False
    return parsed.service != StreamingService.GENERIC


def extract_urls(text: str) -> list[str]:
    """
    Extract all URLs from a text message.
    
    Args:
        text: The text to search for URLs
        
    Returns:
        List of URL strings found in the text
    """
    # Find all URLs in the text
    urls = URL_EXTRACT_PATTERN.findall(text)
    
    # Clean up trailing punctuation that might have been captured
    cleaned_urls = []
    for url in urls:
        # Remove trailing punctuation that's likely not part of the URL
        while url and url[-1] in '.,;:!?)\'">':
            url = url[:-1]
        if url:
            cleaned_urls.append(url)
    
    return cleaned_urls
