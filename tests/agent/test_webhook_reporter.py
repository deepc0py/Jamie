"""Unit tests for webhook reporter (jamie/agent/webhook_reporter.py)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientResponseError
import aiohttp

from jamie.agent.webhook_reporter import WebhookReporter, MAX_RETRIES, TOTAL_TIMEOUT, BACKOFF_DELAYS
from jamie.shared.models import StreamStatus


class TestWebhookReporterInit:
    """Tests for WebhookReporter initialization."""
    
    def test_init_with_url(self):
        """Reporter initializes with webhook URL."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        assert reporter.webhook_url == "https://example.com/webhook"
        assert reporter._session is None
    
    def test_init_without_url(self):
        """Reporter initializes without webhook URL."""
        reporter = WebhookReporter()
        assert reporter.webhook_url is None
        assert reporter._session is None
    
    def test_init_with_none_url(self):
        """Reporter handles explicit None URL."""
        reporter = WebhookReporter(webhook_url=None)
        assert reporter.webhook_url is None


class TestWebhookReporterConstants:
    """Tests for webhook reporter configuration constants."""
    
    def test_max_retries(self):
        """MAX_RETRIES is configured correctly."""
        assert MAX_RETRIES == 3
    
    def test_total_timeout(self):
        """TOTAL_TIMEOUT is configured correctly."""
        assert TOTAL_TIMEOUT == 30
    
    def test_backoff_delays(self):
        """BACKOFF_DELAYS is configured for exponential backoff."""
        assert BACKOFF_DELAYS == [1.0, 2.0, 4.0]
        assert len(BACKOFF_DELAYS) >= MAX_RETRIES - 1


class TestWebhookReporterReport:
    """Tests for WebhookReporter.report() method."""
    
    @pytest.mark.asyncio
    async def test_report_no_webhook_url(self):
        """Report returns True when no webhook URL configured."""
        reporter = WebhookReporter()
        result = await reporter.report(
            session_id="test-123",
            status="streaming",
            message="Test message"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_report_success(self):
        """Report returns True on successful HTTP 200."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        reporter._session = mock_session
        
        result = await reporter.report(
            session_id="test-123",
            status="streaming",
            message="Stream is live"
        )
        
        assert result is True
        mock_session.post.assert_called_once()
        
        # Verify the payload
        call_kwargs = mock_session.post.call_args
        assert call_kwargs[0][0] == "https://example.com/webhook"
        payload = call_kwargs[1]["json"]
        assert payload["session_id"] == "test-123"
        assert payload["status"] == "streaming"
        assert payload["message"] == "Stream is live"
    
    @pytest.mark.asyncio
    async def test_report_with_error_details(self):
        """Report includes error_code and details when provided."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        reporter._session = mock_session
        
        result = await reporter.report(
            session_id="test-123",
            status="failed",
            message="Login failed",
            error_code="AUTH_ERROR",
            details={"reason": "Invalid credentials", "attempts": 3}
        )
        
        assert result is True
        
        payload = mock_session.post.call_args[1]["json"]
        assert payload["error_code"] == "AUTH_ERROR"
        assert payload["details"] == {"reason": "Invalid credentials", "attempts": 3}
    
    @pytest.mark.asyncio
    async def test_report_http_error_retries(self):
        """Report retries on non-200 response and returns False after exhausting retries."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        reporter._session = mock_session
        
        # Mock asyncio.sleep to avoid actual delays
        with patch('jamie.agent.webhook_reporter.asyncio.sleep', new_callable=AsyncMock):
            result = await reporter.report(
                session_id="test-123",
                status="streaming",
                message="Test"
            )
        
        assert result is False
        # Should have been called MAX_RETRIES times
        assert mock_session.post.call_count == MAX_RETRIES
    
    @pytest.mark.asyncio
    async def test_report_network_error_retries(self):
        """Report retries on network exception and returns False after exhausting retries."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_session.closed = False
        
        reporter._session = mock_session
        
        with patch('jamie.agent.webhook_reporter.asyncio.sleep', new_callable=AsyncMock):
            result = await reporter.report(
                session_id="test-123",
                status="streaming",
                message="Test"
            )
        
        assert result is False
        assert mock_session.post.call_count == MAX_RETRIES
    
    @pytest.mark.asyncio
    async def test_report_succeeds_after_retry(self):
        """Report succeeds if a retry attempt succeeds."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        # First call fails, second succeeds
        fail_response = AsyncMock()
        fail_response.status = 500
        fail_response.__aenter__ = AsyncMock(return_value=fail_response)
        fail_response.__aexit__ = AsyncMock(return_value=None)
        
        success_response = AsyncMock()
        success_response.status = 200
        success_response.__aenter__ = AsyncMock(return_value=success_response)
        success_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(side_effect=[fail_response, success_response])
        mock_session.closed = False
        
        reporter._session = mock_session
        
        with patch('jamie.agent.webhook_reporter.asyncio.sleep', new_callable=AsyncMock):
            result = await reporter.report(
                session_id="test-123",
                status="streaming",
                message="Test"
            )
        
        assert result is True
        assert mock_session.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_report_invalid_status_fallback(self):
        """Report handles invalid status by falling back to STREAMING."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        reporter._session = mock_session
        
        # Pass an invalid status value
        result = await reporter.report(
            session_id="test-123",
            status="unknown_invalid_status",
            message="Test"
        )
        
        assert result is True
        
        # Should have fallen back to streaming status
        payload = mock_session.post.call_args[1]["json"]
        assert payload["status"] == StreamStatus.STREAMING.value
    
    @pytest.mark.asyncio
    async def test_report_all_valid_statuses(self):
        """Report correctly maps all valid StreamStatus values."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        reporter._session = mock_session
        
        for status in StreamStatus:
            result = await reporter.report(
                session_id="test-123",
                status=status.value,
                message=f"Status: {status.value}"
            )
            assert result is True
            
            payload = mock_session.post.call_args[1]["json"]
            assert payload["status"] == status.value


class TestWebhookReporterSession:
    """Tests for WebhookReporter session management."""
    
    @pytest.mark.asyncio
    async def test_get_session_creates_new(self):
        """_get_session creates new session when none exists."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        with patch('aiohttp.ClientSession') as mock_cls:
            mock_session = MagicMock()
            mock_session.closed = False
            mock_cls.return_value = mock_session
            
            session = await reporter._get_session()
            
            assert session is mock_session
            mock_cls.assert_called_once()
            # Verify timeout is set on session creation
            call_kwargs = mock_cls.call_args
            assert call_kwargs[1]["timeout"].total == TOTAL_TIMEOUT
    
    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self):
        """_get_session reuses existing open session."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        existing_session = MagicMock()
        existing_session.closed = False
        reporter._session = existing_session
        
        with patch('aiohttp.ClientSession') as mock_cls:
            session = await reporter._get_session()
            
            assert session is existing_session
            mock_cls.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_session_creates_new_if_closed(self):
        """_get_session creates new session if existing is closed."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        closed_session = MagicMock()
        closed_session.closed = True
        reporter._session = closed_session
        
        with patch('aiohttp.ClientSession') as mock_cls:
            new_session = MagicMock()
            new_session.closed = False
            mock_cls.return_value = new_session
            
            session = await reporter._get_session()
            
            assert session is new_session
            mock_cls.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_session(self):
        """close() closes the session."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        mock_session = AsyncMock()
        mock_session.closed = False
        reporter._session = mock_session
        
        await reporter.close()
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_no_session(self):
        """close() handles no session gracefully."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        # Should not raise
        await reporter.close()
    
    @pytest.mark.asyncio
    async def test_close_already_closed(self):
        """close() handles already closed session."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        mock_session = AsyncMock()
        mock_session.closed = True
        reporter._session = mock_session
        
        # Should not raise and should not call close again
        await reporter.close()
        mock_session.close.assert_not_called()


class TestWebhookReporterContextManager:
    """Tests for WebhookReporter async context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager_enter(self):
        """Context manager returns self on enter."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        result = await reporter.__aenter__()
        
        assert result is reporter
    
    @pytest.mark.asyncio
    async def test_context_manager_exit_closes(self):
        """Context manager closes session on exit."""
        reporter = WebhookReporter(webhook_url="https://example.com")
        
        mock_session = AsyncMock()
        mock_session.closed = False
        reporter._session = mock_session
        
        await reporter.__aexit__(None, None, None)
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_full_usage(self):
        """Context manager works correctly in async with statement."""
        with patch('aiohttp.ClientSession') as mock_cls:
            mock_session_instance = AsyncMock()
            mock_session_instance.closed = False
            mock_cls.return_value = mock_session_instance
            
            async with WebhookReporter(webhook_url="https://example.com") as reporter:
                assert reporter.webhook_url == "https://example.com"
                # Force session creation
                await reporter._get_session()
            
            # Session should be closed after exiting context
            mock_session_instance.close.assert_called_once()


class TestWebhookReporterPayload:
    """Tests for webhook payload structure."""
    
    @pytest.mark.asyncio
    async def test_payload_has_timestamp(self):
        """Payload includes timestamp."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.closed = False
        
        reporter._session = mock_session
        
        await reporter.report(
            session_id="test-123",
            status="streaming",
            message="Test"
        )
        
        payload = mock_session.post.call_args[1]["json"]
        assert "timestamp" in payload
        # Timestamp should be ISO format string
        assert isinstance(payload["timestamp"], str)
    
    @pytest.mark.asyncio
    async def test_session_timeout_configured(self):
        """Session is created with correct timeout."""
        reporter = WebhookReporter(webhook_url="https://example.com/webhook")
        
        with patch('aiohttp.ClientSession') as mock_cls:
            mock_session = MagicMock()
            mock_session.closed = False
            mock_cls.return_value = mock_session
            
            await reporter._get_session()
            
            # Verify timeout is set correctly
            call_kwargs = mock_cls.call_args
            timeout = call_kwargs[1]["timeout"]
            assert timeout.total == TOTAL_TIMEOUT
