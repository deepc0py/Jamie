"""Unit tests for URL pattern matching."""

import pytest

from jamie.bot.url_patterns import (
    StreamingService,
    ParsedURL,
    parse_url,
    is_supported_url,
    extract_urls,
)


class TestStreamingServiceEnum:
    """Tests for StreamingService enum."""
    
    def test_enum_values(self):
        """Verify all expected services exist."""
        assert StreamingService.YOUTUBE == "youtube"
        assert StreamingService.TWITCH == "twitch"
        assert StreamingService.VIMEO == "vimeo"
        assert StreamingService.WIKIPEDIA == "wikipedia"
        assert StreamingService.GENERIC == "generic"
    
    def test_enum_is_string(self):
        """Verify enum values are strings."""
        assert isinstance(StreamingService.YOUTUBE.value, str)
        # str(Enum) returns the class representation, but .value is the string
        assert StreamingService.YOUTUBE.value == "youtube"


class TestYouTubePatterns:
    """Tests for YouTube URL parsing."""
    
    def test_standard_watch_url(self):
        """Parse standard youtube.com/watch?v= URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.normalized == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    def test_short_url(self):
        """Parse youtu.be short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
        assert result.video_id == "dQw4w9WgXcQ"
    
    def test_embed_url(self):
        """Parse youtube.com/embed/ URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
        assert result.video_id == "dQw4w9WgXcQ"
    
    def test_shorts_url(self):
        """Parse youtube.com/shorts/ URL."""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
        assert result.video_id == "dQw4w9WgXcQ"
    
    def test_live_url(self):
        """Parse youtube.com/live/ URL."""
        url = "https://www.youtube.com/live/dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
        assert result.video_id == "dQw4w9WgXcQ"
    
    def test_without_https(self):
        """Parse URL without https://."""
        url = "youtube.com/watch?v=dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
        assert result.video_id == "dQw4w9WgXcQ"
    
    def test_without_www(self):
        """Parse URL without www."""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.YOUTUBE
    
    def test_video_id_with_hyphen_underscore(self):
        """Parse video ID with hyphen and underscore."""
        url = "https://www.youtube.com/watch?v=abc-_123XYZ"
        result = parse_url(url)
        
        assert result is not None
        assert result.video_id == "abc-_123XYZ"


class TestTwitchPatterns:
    """Tests for Twitch URL parsing."""
    
    def test_channel_url(self):
        """Parse twitch.tv/channel URL."""
        url = "https://www.twitch.tv/ninja"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.TWITCH
        assert result.video_id == "ninja"
        assert result.normalized == "https://www.twitch.tv/ninja"
    
    def test_channel_with_underscores(self):
        """Parse channel name with underscores."""
        url = "https://twitch.tv/some_streamer_name"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.TWITCH
        assert result.video_id == "some_streamer_name"
    
    def test_channel_with_numbers(self):
        """Parse channel name with numbers."""
        url = "https://twitch.tv/player123"
        result = parse_url(url)
        
        assert result is not None
        assert result.video_id == "player123"
    
    def test_without_https(self):
        """Parse URL without https://."""
        url = "twitch.tv/streamer"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.TWITCH


class TestVimeoPatterns:
    """Tests for Vimeo URL parsing."""
    
    def test_standard_url(self):
        """Parse vimeo.com/video_id URL."""
        url = "https://vimeo.com/123456789"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.VIMEO
        assert result.video_id == "123456789"
        assert result.normalized == "https://vimeo.com/123456789"
    
    def test_player_embed_url(self):
        """Parse player.vimeo.com/video/ URL."""
        url = "https://player.vimeo.com/video/123456789"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.VIMEO
        assert result.video_id == "123456789"
    
    def test_without_https(self):
        """Parse URL without https://."""
        url = "vimeo.com/987654321"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.VIMEO


class TestWikipediaPatterns:
    """Tests for Wikipedia URL parsing."""
    
    def test_english_wikipedia(self):
        """Parse en.wikipedia.org URL."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.WIKIPEDIA
        assert result.video_id == "Python_(programming_language)"
    
    def test_other_language_wikipedia(self):
        """Parse non-English Wikipedia URL."""
        url = "https://de.wikipedia.org/wiki/Katze"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.WIKIPEDIA
        assert "Katze" in result.video_id
    
    def test_wikipedia_without_language(self):
        """Parse wikipedia.org without language prefix."""
        url = "https://wikipedia.org/wiki/Main_Page"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.WIKIPEDIA


class TestGenericURLs:
    """Tests for generic URL handling."""
    
    def test_generic_https_url(self):
        """Parse any HTTPS URL as generic."""
        url = "https://example.com/some/path"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.GENERIC
        assert result.video_id is None
        assert result.normalized == url
    
    def test_generic_http_url(self):
        """Parse HTTP URL as generic."""
        url = "http://example.org/page.html"
        result = parse_url(url)
        
        assert result is not None
        assert result.service == StreamingService.GENERIC
    
    def test_invalid_url_returns_none(self):
        """Invalid URLs should return None."""
        assert parse_url("not a url") is None
        assert parse_url("ftp://files.example.com") is None
        assert parse_url("") is None
        assert parse_url("   ") is None


class TestIsSupportedURL:
    """Tests for is_supported_url function."""
    
    def test_youtube_is_supported(self):
        """YouTube URLs are supported."""
        assert is_supported_url("https://youtube.com/watch?v=dQw4w9WgXcQ") is True
    
    def test_twitch_is_supported(self):
        """Twitch URLs are supported."""
        assert is_supported_url("https://twitch.tv/ninja") is True
    
    def test_vimeo_is_supported(self):
        """Vimeo URLs are supported."""
        assert is_supported_url("https://vimeo.com/123456") is True
    
    def test_wikipedia_is_supported(self):
        """Wikipedia URLs are supported."""
        assert is_supported_url("https://en.wikipedia.org/wiki/Test") is True
    
    def test_generic_not_supported(self):
        """Generic URLs are not 'supported' (returns False)."""
        assert is_supported_url("https://example.com/video") is False
    
    def test_invalid_url_not_supported(self):
        """Invalid URLs are not supported."""
        assert is_supported_url("not a url") is False


class TestExtractURLs:
    """Tests for extract_urls function."""
    
    def test_single_url(self):
        """Extract single URL from text."""
        text = "Check out this video: https://youtube.com/watch?v=dQw4w9WgXcQ"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert urls[0] == "https://youtube.com/watch?v=dQw4w9WgXcQ"
    
    def test_multiple_urls(self):
        """Extract multiple URLs from text."""
        text = "Here's https://youtube.com/watch?v=abc123 and also https://twitch.tv/ninja"
        urls = extract_urls(text)
        
        assert len(urls) == 2
        assert "youtube.com" in urls[0]
        assert "twitch.tv" in urls[1]
    
    def test_url_with_trailing_punctuation(self):
        """URLs with trailing punctuation should be cleaned."""
        text = "Check this out: https://example.com/path."
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert urls[0] == "https://example.com/path"
    
    def test_url_in_parentheses(self):
        """Extract URL from parentheses, cleaning trailing paren."""
        text = "(see https://example.com/page)"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert urls[0] == "https://example.com/page"
    
    def test_no_urls(self):
        """Return empty list when no URLs present."""
        text = "This is just regular text with no links."
        urls = extract_urls(text)
        
        assert urls == []
    
    def test_empty_string(self):
        """Return empty list for empty string."""
        urls = extract_urls("")
        assert urls == []
    
    def test_http_urls(self):
        """Extract HTTP (not HTTPS) URLs."""
        text = "Old link: http://example.com/old"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert urls[0] == "http://example.com/old"
    
    def test_complex_youtube_url(self):
        """Extract YouTube URL with additional parameters."""
        text = "Watch at https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=60s please"
        urls = extract_urls(text)
        
        assert len(urls) == 1
        assert "dQw4w9WgXcQ" in urls[0]


class TestParsedURLDataclass:
    """Tests for ParsedURL dataclass."""
    
    def test_dataclass_fields(self):
        """Verify dataclass has expected fields."""
        parsed = ParsedURL(
            original="https://youtube.com/watch?v=test",
            service=StreamingService.YOUTUBE,
            video_id="test",
            normalized="https://www.youtube.com/watch?v=test"
        )
        
        assert parsed.original == "https://youtube.com/watch?v=test"
        assert parsed.service == StreamingService.YOUTUBE
        assert parsed.video_id == "test"
        assert parsed.normalized == "https://www.youtube.com/watch?v=test"
    
    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        parsed = ParsedURL(
            original="https://example.com",
            service=StreamingService.GENERIC
        )
        
        assert parsed.video_id is None
        assert parsed.normalized is None
