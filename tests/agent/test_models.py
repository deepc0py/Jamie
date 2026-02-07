"""Unit tests for shared API models (jamie/shared/models.py)."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from jamie.shared.models import (
    StreamStatus,
    StreamRequest,
    StreamResponse,
    StatusUpdate,
    StopRequest,
    HealthResponse,
)


class TestStreamStatus:
    """Tests for StreamStatus enum."""
    
    def test_all_statuses_exist(self):
        """All expected status values are defined."""
        expected = [
            "pending", "starting", "logging_in", "joining_voice",
            "opening_url", "sharing_screen", "streaming",
            "stopping", "stopped", "failed"
        ]
        for status in expected:
            assert StreamStatus(status) is not None
    
    def test_status_is_string_enum(self):
        """StreamStatus values are strings."""
        assert StreamStatus.PENDING.value == "pending"
        assert StreamStatus.STREAMING.value == "streaming"
        assert StreamStatus.FAILED.value == "failed"
        # String enum allows direct comparison
        assert StreamStatus.PENDING == "pending"
    
    def test_invalid_status_raises(self):
        """Invalid status value raises ValueError."""
        with pytest.raises(ValueError):
            StreamStatus("invalid_status")


class TestStreamRequest:
    """Tests for StreamRequest model."""
    
    @pytest.fixture
    def valid_request_data(self):
        """Valid StreamRequest data."""
        return {
            "session_id": "sess-123",
            "url": "https://youtube.com/watch?v=abc123",
            "guild_id": "123456789",
            "channel_id": "987654321",
            "channel_name": "General",
            "requester_id": "111222333",
        }
    
    def test_valid_request(self, valid_request_data):
        """Valid data creates StreamRequest successfully."""
        request = StreamRequest(**valid_request_data)
        assert request.session_id == "sess-123"
        assert str(request.url) == "https://youtube.com/watch?v=abc123"
        assert request.guild_id == "123456789"
        assert request.channel_id == "987654321"
        assert request.channel_name == "General"
        assert request.requester_id == "111222333"
        assert request.webhook_url is None
    
    def test_with_webhook_url(self, valid_request_data):
        """Request with webhook_url is valid."""
        valid_request_data["webhook_url"] = "https://example.com/webhook"
        request = StreamRequest(**valid_request_data)
        assert str(request.webhook_url) == "https://example.com/webhook"
    
    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc:
            StreamRequest(session_id="test")
        errors = exc.value.errors()
        # Should have errors for url, guild_id, channel_id, channel_name, requester_id
        assert len(errors) >= 4
    
    def test_invalid_url(self, valid_request_data):
        """Invalid URL raises ValidationError."""
        valid_request_data["url"] = "not-a-url"
        with pytest.raises(ValidationError) as exc:
            StreamRequest(**valid_request_data)
        assert any("url" in str(e["loc"]) for e in exc.value.errors())
    
    def test_invalid_webhook_url(self, valid_request_data):
        """Invalid webhook URL raises ValidationError."""
        valid_request_data["webhook_url"] = "invalid"
        with pytest.raises(ValidationError) as exc:
            StreamRequest(**valid_request_data)
        assert any("webhook_url" in str(e["loc"]) for e in exc.value.errors())


class TestStreamResponse:
    """Tests for StreamResponse model."""
    
    def test_valid_response(self):
        """Valid StreamResponse creation."""
        response = StreamResponse(
            session_id="sess-123",
            status=StreamStatus.STREAMING,
            message="All good"
        )
        assert response.session_id == "sess-123"
        assert response.status == StreamStatus.STREAMING
        assert response.message == "All good"
    
    def test_status_as_string(self):
        """Status can be provided as string."""
        response = StreamResponse(
            session_id="sess-123",
            status="pending",
            message="Waiting"
        )
        assert response.status == StreamStatus.PENDING
    
    def test_missing_fields_raises(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            StreamResponse(session_id="test")


class TestStatusUpdate:
    """Tests for StatusUpdate model."""
    
    def test_valid_status_update(self):
        """Valid StatusUpdate creation."""
        update = StatusUpdate(
            session_id="sess-123",
            status=StreamStatus.STREAMING,
            message="Stream is live"
        )
        assert update.session_id == "sess-123"
        assert update.status == StreamStatus.STREAMING
        assert update.message == "Stream is live"
        assert isinstance(update.timestamp, datetime)
        assert update.error_code is None
        assert update.details is None
    
    def test_with_error_details(self):
        """StatusUpdate with error code and details."""
        update = StatusUpdate(
            session_id="sess-123",
            status=StreamStatus.FAILED,
            message="Login failed",
            error_code="AUTH_ERROR",
            details={"reason": "Invalid credentials"}
        )
        assert update.error_code == "AUTH_ERROR"
        assert update.details == {"reason": "Invalid credentials"}
    
    def test_timestamp_auto_generated(self):
        """Timestamp is auto-generated if not provided."""
        before = datetime.utcnow()
        update = StatusUpdate(
            session_id="sess-123",
            status=StreamStatus.PENDING,
            message="Waiting"
        )
        after = datetime.utcnow()
        assert before <= update.timestamp <= after
    
    def test_custom_timestamp(self):
        """Custom timestamp is accepted."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        update = StatusUpdate(
            session_id="sess-123",
            status=StreamStatus.PENDING,
            message="Waiting",
            timestamp=custom_time
        )
        assert update.timestamp == custom_time


class TestStopRequest:
    """Tests for StopRequest model."""
    
    def test_valid_stop_request(self):
        """Valid StopRequest creation."""
        request = StopRequest(
            session_id="sess-123",
            requester_id="user-456"
        )
        assert request.session_id == "sess-123"
        assert request.requester_id == "user-456"
    
    def test_missing_fields_raises(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            StopRequest(session_id="test")
        with pytest.raises(ValidationError):
            StopRequest(requester_id="user")


class TestHealthResponse:
    """Tests for HealthResponse model."""
    
    def test_default_values(self):
        """HealthResponse has sensible defaults."""
        response = HealthResponse()
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.active_sessions == 0
    
    def test_custom_values(self):
        """HealthResponse accepts custom values."""
        response = HealthResponse(
            status="degraded",
            version="1.0.0",
            active_sessions=5
        )
        assert response.status == "degraded"
        assert response.version == "1.0.0"
        assert response.active_sessions == 5
    
    def test_serialization(self):
        """HealthResponse serializes to dict correctly."""
        response = HealthResponse(active_sessions=3)
        data = response.model_dump()
        # Check core fields
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert data["active_sessions"] == 3
        # Metrics fields default to None
        assert data["uptime_seconds"] is None
        assert data["streams_total"] is None
        assert data["streams_success"] is None
        assert data["streams_failed"] is None
        assert data["success_rate_percent"] is None
    
    def test_serialization_with_metrics(self):
        """HealthResponse with metrics serializes correctly."""
        response = HealthResponse(
            active_sessions=5,
            uptime_seconds=3600.0,
            streams_total=100,
            streams_success=95,
            streams_failed=5,
            success_rate_percent=95.0
        )
        data = response.model_dump()
        assert data["active_sessions"] == 5
        assert data["uptime_seconds"] == 3600.0
        assert data["streams_total"] == 100
        assert data["streams_success"] == 95
        assert data["streams_failed"] == 5
        assert data["success_rate_percent"] == 95.0
