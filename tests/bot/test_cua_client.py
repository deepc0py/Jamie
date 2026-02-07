"""Unit tests for CUAClient with mocked responses."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from jamie.bot.cua_client import CUAClient, CUAClientConfig, CUAClientError
from jamie.shared.errors import ErrorCode
from jamie.shared.models import (
    HealthResponse,
    StreamRequest,
    StreamResponse,
    StreamStatus,
)


class TestCUAClientConfig:
    """Tests for CUAClientConfig."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = CUAClientConfig()
        
        assert config.base_url == "http://localhost:8000"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_custom_values(self):
        """Config should accept custom values."""
        config = CUAClientConfig(
            base_url="http://cua:9000",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
        )
        
        assert config.base_url == "http://cua:9000"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0


class TestCUAClientInit:
    """Tests for CUAClient initialization."""

    def test_default_config(self):
        """CUAClient should use default config if none provided."""
        client = CUAClient()
        
        assert client.config.base_url == "http://localhost:8000"
        assert client._session is None

    def test_custom_config(self):
        """CUAClient should use provided config."""
        config = CUAClientConfig(base_url="http://custom:8080")
        client = CUAClient(config)
        
        assert client.config.base_url == "http://custom:8080"


class TestCUAClientHealthCheck:
    """Tests for CUAClient.health_check."""

    @pytest.fixture
    def client(self):
        """Create a CUAClient with minimal retries for faster tests."""
        config = CUAClientConfig(max_retries=1, retry_delay=0.01)
        return CUAClient(config)

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """health_check should return HealthResponse on success."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": "healthy",
            "version": "1.0.0",
            "active_sessions": 2,
        })
        
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client.health_check()
        
        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"
        assert result.version == "1.0.0"
        assert result.active_sessions == 2

    @pytest.mark.asyncio
    async def test_health_check_non_200_raises(self, client):
        """health_check should raise CUAClientError on non-200 status."""
        mock_response = AsyncMock()
        mock_response.status = 503
        
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(CUAClientError) as exc_info:
                await client.health_check()
        
        assert exc_info.value.code == ErrorCode.CUA_UNAVAILABLE
        assert "503" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_health_check_connection_error_raises(self, client):
        """health_check should raise CUAClientError on connection error."""
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(side_effect=aiohttp.ClientError("Connection refused")),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(CUAClientError) as exc_info:
                await client.health_check()
        
        assert exc_info.value.code == ErrorCode.CUA_UNAVAILABLE


class TestCUAClientStartStream:
    """Tests for CUAClient.start_stream."""

    @pytest.fixture
    def client(self):
        """Create a CUAClient with minimal retries for faster tests."""
        config = CUAClientConfig(max_retries=1, retry_delay=0.01)
        return CUAClient(config)

    @pytest.fixture
    def stream_request(self):
        """Create a sample StreamRequest."""
        return StreamRequest(
            session_id="test-session-123",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            requester_id="user123",
            webhook_url="http://localhost:5000/status",
        )

    @pytest.mark.asyncio
    async def test_start_stream_success(self, client, stream_request):
        """start_stream should return StreamResponse on success."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "session_id": "test-session-123",
            "status": "pending",
            "message": "Stream request accepted",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client.start_stream(stream_request)
        
        assert isinstance(result, StreamResponse)
        assert result.session_id == "test-session-123"
        assert result.status == StreamStatus.PENDING
        assert result.message == "Stream request accepted"

    @pytest.mark.asyncio
    async def test_start_stream_409_already_streaming(self, client, stream_request):
        """start_stream should raise ALREADY_STREAMING on 409."""
        mock_response = AsyncMock()
        mock_response.status = 409
        mock_response.json = AsyncMock(return_value={
            "detail": "User already has an active stream",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(CUAClientError) as exc_info:
                await client.start_stream(stream_request)
        
        assert exc_info.value.code == ErrorCode.ALREADY_STREAMING

    @pytest.mark.asyncio
    async def test_start_stream_400_invalid_url(self, client, stream_request):
        """start_stream should raise INVALID_URL on 400."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={
            "detail": "Invalid URL provided",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(CUAClientError) as exc_info:
                await client.start_stream(stream_request)
        
        assert exc_info.value.code == ErrorCode.INVALID_URL

    @pytest.mark.asyncio
    async def test_start_stream_500_cua_unavailable(self, client, stream_request):
        """start_stream should raise CUA_UNAVAILABLE on 500."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(return_value={
            "detail": "Internal server error",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(CUAClientError) as exc_info:
                await client.start_stream(stream_request)
        
        assert exc_info.value.code == ErrorCode.CUA_UNAVAILABLE


class TestCUAClientStopStream:
    """Tests for CUAClient.stop_stream."""

    @pytest.fixture
    def client(self):
        """Create a CUAClient with minimal retries for faster tests."""
        config = CUAClientConfig(max_retries=1, retry_delay=0.01)
        return CUAClient(config)

    @pytest.mark.asyncio
    async def test_stop_stream_success(self, client):
        """stop_stream should return StreamResponse on success."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "session_id": "test-session-123",
            "status": "stopped",
            "message": "Stream stopped successfully",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client.stop_stream("test-session-123", "user123")
        
        assert isinstance(result, StreamResponse)
        assert result.session_id == "test-session-123"
        assert result.status == StreamStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_stream_204_success(self, client):
        """stop_stream should handle 204 response."""
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.json = AsyncMock(return_value={
            "session_id": "test-session-123",
            "status": "stopped",
            "message": "Stream stopped",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client.stop_stream("test-session-123", "user123")
        
        assert result.status == StreamStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_stream_failure(self, client):
        """stop_stream should raise CUAClientError on failure."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={
            "detail": "Session not found",
        })
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None),
        ))
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(CUAClientError) as exc_info:
                await client.stop_stream("unknown-session", "user123")
        
        assert exc_info.value.code == ErrorCode.CUA_UNAVAILABLE


class TestCUAClientRetry:
    """Tests for CUAClient retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Client should retry on transient errors."""
        config = CUAClientConfig(max_retries=3, retry_delay=0.01)
        client = CUAClient(config)
        
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise CUAClientError(
                    code=ErrorCode.CUA_UNAVAILABLE,
                    message="Transient error",
                )
            return HealthResponse(status="healthy", version="1.0.0", active_sessions=0)
        
        result = await client._retry(mock_operation)
        
        assert call_count == 3
        assert result.status == "healthy"

    @pytest.mark.asyncio
    async def test_no_retry_on_user_error(self):
        """Client should not retry on user errors."""
        config = CUAClientConfig(max_retries=3, retry_delay=0.01)
        client = CUAClient(config)
        
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            raise CUAClientError(
                code=ErrorCode.INVALID_URL,
                message="User error - not retryable",
            )
        
        with pytest.raises(CUAClientError) as exc_info:
            await client._retry(mock_operation)
        
        # Should only be called once since INVALID_URL is not retryable
        assert call_count == 1
        assert exc_info.value.code == ErrorCode.INVALID_URL

    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        """Client should raise after exhausting retries."""
        config = CUAClientConfig(max_retries=2, retry_delay=0.01)
        client = CUAClient(config)
        
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            raise CUAClientError(
                code=ErrorCode.CUA_UNAVAILABLE,
                message="Always fails",
            )
        
        with pytest.raises(CUAClientError):
            await client._retry(mock_operation)
        
        assert call_count == 2  # max_retries attempts


class TestCUAClientContextManager:
    """Tests for CUAClient async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self):
        """Context manager should close session on exit."""
        client = CUAClient()
        
        # Create a mock session
        mock_session = AsyncMock()
        mock_session.closed = False
        client._session = mock_session
        
        async with client:
            pass
        
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_when_no_session(self):
        """close() should not fail when no session exists."""
        client = CUAClient()
        assert client._session is None
        
        # Should not raise
        await client.close()

    @pytest.mark.asyncio
    async def test_close_when_session_already_closed(self):
        """close() should not fail when session already closed."""
        client = CUAClient()
        
        mock_session = MagicMock()
        mock_session.closed = True
        client._session = mock_session
        
        # Should not raise or call close again
        await client.close()
        mock_session.close.assert_not_called()


class TestCUAClientError:
    """Tests for CUAClientError exception."""

    def test_error_inherits_from_jamie_error(self):
        """CUAClientError should inherit from JamieError."""
        from jamie.shared.errors import JamieError
        
        error = CUAClientError(
            code=ErrorCode.CUA_UNAVAILABLE,
            message="Test error",
        )
        
        assert isinstance(error, JamieError)

    def test_error_has_code_and_message(self):
        """CUAClientError should have code and message."""
        error = CUAClientError(
            code=ErrorCode.INVALID_URL,
            message="Invalid URL provided",
        )
        
        assert error.code == ErrorCode.INVALID_URL
        assert error.message == "Invalid URL provided"

    def test_error_string_representation(self):
        """CUAClientError should have readable string representation."""
        error = CUAClientError(
            code=ErrorCode.CUA_UNAVAILABLE,
            message="Connection refused",
        )
        
        assert "CUA_UNAVAILABLE" in str(error)
        assert "Connection refused" in str(error)
