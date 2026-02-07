"""Unit tests for API controller (jamie/agent/controller.py)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import asyncio

from jamie.shared.models import StreamStatus


class TestControllerEndpoints:
    """Tests for controller HTTP endpoints."""
    
    @pytest.fixture
    def app(self):
        """Get fresh app instance with cleared state."""
        from jamie.agent import controller
        controller._agents.clear()
        controller._agent_tasks.clear()
        controller._config = None
        return controller.app
    
    @pytest.fixture
    def client(self, app):
        """Synchronous test client."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_stream_request(self):
        """Valid stream request payload."""
        return {
            "session_id": "test-session-001",
            "url": "https://youtube.com/watch?v=test",
            "guild_id": "123456789",
            "channel_id": "987654321",
            "channel_name": "General",
            "requester_id": "111222333",
            "webhook_url": "https://example.com/webhook"
        }
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config object."""
        config = MagicMock()
        config.discord_email.get_secret_value.return_value = "test@test.com"
        config.discord_password.get_secret_value.return_value = "password"
        config.model = "test-model"
        config.max_budget_per_session = 2.0
        config.sandbox_image = "test-image"
        config.display_resolution = "1024x768"
        return config
    
    def test_health_check(self, client):
        """Health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert data["active_sessions"] == 0
    
    def test_health_check_with_active_sessions(self, app):
        """Health endpoint reflects active session count."""
        from jamie.agent import controller
        
        # Directly add a mock agent to simulate an active session
        mock_agent = MagicMock()
        controller._agents["test-session"] = mock_agent
        
        try:
            client = TestClient(app)
            health_response = client.get("/health")
            assert health_response.json()["active_sessions"] == 1
        finally:
            controller._agents.clear()
    
    @patch('jamie.agent.controller.StreamingAgent')
    @patch('jamie.agent.controller.get_config')
    def test_start_stream_success(self, mock_get_config, mock_agent_cls, client, valid_stream_request, mock_config):
        """Start stream endpoint accepts valid request."""
        mock_get_config.return_value = mock_config
        
        mock_agent = AsyncMock()
        mock_agent_cls.return_value = mock_agent
        
        response = client.post("/stream", json=valid_stream_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-001"
        assert data["status"] == StreamStatus.PENDING.value
        assert "accepted" in data["message"].lower()
    
    def test_start_stream_duplicate_session(self, app, valid_stream_request, mock_config):
        """Duplicate session ID returns 409 Conflict."""
        from jamie.agent import controller
        
        # Pre-register a session to simulate an active one
        mock_agent = MagicMock()
        controller._agents["test-session-001"] = mock_agent
        
        try:
            client = TestClient(app)
            
            with patch.object(controller, 'get_config', return_value=mock_config):
                # Request with same session_id should fail
                response = client.post("/stream", json=valid_stream_request)
                assert response.status_code == 409
                assert "already exists" in response.json()["detail"]
        finally:
            controller._agents.clear()
    
    def test_start_stream_invalid_url(self, client):
        """Invalid URL in request returns 422."""
        invalid_request = {
            "session_id": "test-session",
            "url": "not-a-valid-url",
            "guild_id": "123",
            "channel_id": "456",
            "channel_name": "Test",
            "requester_id": "789"
        }
        response = client.post("/stream", json=invalid_request)
        assert response.status_code == 422
    
    def test_start_stream_missing_fields(self, client):
        """Missing required fields returns 422."""
        incomplete_request = {"session_id": "test"}
        response = client.post("/stream", json=incomplete_request)
        assert response.status_code == 422
    
    def test_stop_stream_success(self, app, mock_config):
        """Stop stream endpoint stops active session."""
        from jamie.agent import controller
        
        # Pre-register a mock agent
        mock_agent = AsyncMock()
        mock_agent.stop = AsyncMock()
        controller._agents["test-session-001"] = mock_agent
        
        # Create a non-done task mock
        mock_task = MagicMock()
        mock_task.done.return_value = False
        controller._agent_tasks["test-session-001"] = mock_task
        
        try:
            client = TestClient(app)
            
            stop_request = {
                "session_id": "test-session-001",
                "requester_id": "111222333"
            }
            response = client.post("/stop/test-session-001", json=stop_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-001"
            assert data["status"] == StreamStatus.STOPPED.value
            
            # Verify agent.stop was called
            mock_agent.stop.assert_called_once()
            # Verify task was cancelled
            mock_task.cancel.assert_called_once()
        finally:
            controller._agents.clear()
            controller._agent_tasks.clear()
    
    def test_stop_stream_not_found(self, client):
        """Stop non-existent session returns 404."""
        stop_request = {
            "session_id": "nonexistent",
            "requester_id": "111222333"
        }
        response = client.post("/stop/nonexistent", json=stop_request)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_sessions_empty(self, client):
        """List sessions returns empty when no active sessions."""
        response = client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["sessions"] == []
    
    def test_list_sessions_with_active(self, app):
        """List sessions returns active session IDs."""
        from jamie.agent import controller
        
        # Pre-register mock agents
        controller._agents["test-session-001"] = MagicMock()
        controller._agents["test-session-002"] = MagicMock()
        
        try:
            client = TestClient(app)
            
            response = client.get("/sessions")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            assert "test-session-001" in data["sessions"]
            assert "test-session-002" in data["sessions"]
        finally:
            controller._agents.clear()


class TestAgentContextCreation:
    """Tests for AgentContext creation in controller."""
    
    @patch('jamie.agent.controller.StreamingAgent')
    @patch('jamie.agent.controller.get_config')
    def test_agent_context_populated_correctly(self, mock_get_config, mock_agent_cls):
        """Agent is created with correct context from request and config."""
        from jamie.agent import controller
        controller._agents.clear()
        controller._agent_tasks.clear()
        controller._config = None
        
        # Setup mocks
        mock_config = MagicMock()
        mock_config.discord_email.get_secret_value.return_value = "test@test.com"
        mock_config.discord_password.get_secret_value.return_value = "secret123"
        mock_config.model = "claude-test"
        mock_config.max_budget_per_session = 5.0
        mock_config.sandbox_image = "custom-image:v1"
        mock_config.display_resolution = "1920x1080"
        mock_get_config.return_value = mock_config
        
        mock_agent = AsyncMock()
        mock_agent_cls.return_value = mock_agent
        
        client = TestClient(controller.app)
        
        request = {
            "session_id": "ctx-test",
            "url": "https://test.com/video",
            "guild_id": "guild-123",
            "channel_id": "channel-456",
            "channel_name": "Voice Channel",
            "requester_id": "user-789",
            "webhook_url": "https://webhook.test/status"
        }
        
        client.post("/stream", json=request)
        
        # Verify StreamingAgent was called with correct context
        mock_agent_cls.assert_called_once()
        context = mock_agent_cls.call_args[0][0]
        
        assert context.session_id == "ctx-test"
        assert context.url == "https://test.com/video"
        assert context.guild_id == "guild-123"
        assert context.channel_id == "channel-456"
        assert context.channel_name == "Voice Channel"
        assert context.discord_email == "test@test.com"
        assert context.discord_password == "secret123"
        assert context.model == "claude-test"
        assert context.max_budget == 5.0
        assert context.sandbox_image == "custom-image:v1"
        assert context.display_resolution == "1920x1080"
        assert context.webhook_url == "https://webhook.test/status"


class TestBackgroundTaskCleanup:
    """Tests for agent background task handling."""
    
    @pytest.mark.asyncio
    @patch('jamie.agent.controller.StreamingAgent')
    @patch('jamie.agent.controller.get_config')
    async def test_agent_cleanup_on_completion(self, mock_get_config, mock_agent_cls):
        """Agent is cleaned up from registry when task completes."""
        from jamie.agent import controller
        controller._agents.clear()
        controller._agent_tasks.clear()
        controller._config = None
        
        # Setup mocks
        mock_config = MagicMock()
        mock_config.discord_email.get_secret_value.return_value = "test@test.com"
        mock_config.discord_password.get_secret_value.return_value = "password"
        mock_config.model = "test-model"
        mock_config.max_budget_per_session = 2.0
        mock_config.sandbox_image = "test-image"
        mock_config.display_resolution = "1024x768"
        mock_get_config.return_value = mock_config
        
        # Agent that completes immediately
        mock_agent = AsyncMock()
        mock_agent.start = AsyncMock()
        mock_agent_cls.return_value = mock_agent
        
        transport = ASGITransport(app=controller.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            request = {
                "session_id": "cleanup-test",
                "url": "https://test.com/video",
                "guild_id": "123",
                "channel_id": "456",
                "channel_name": "Test",
                "requester_id": "789"
            }
            
            response = await ac.post("/stream", json=request)
            assert response.status_code == 200
            
            # Wait for background task to complete
            await asyncio.sleep(0.1)
            
            # Agent should be cleaned up after task completes
            assert "cleanup-test" not in controller._agents


class TestControllerStartup:
    """Tests for controller startup behavior."""
    
    def test_startup_initializes_logging(self):
        """Startup event initializes logging."""
        from jamie.agent import controller
        
        # Trigger startup
        with TestClient(controller.app):
            # Just verify no errors during startup
            pass


class TestStreamCreatesAgentTask:
    """Tests for verifying agent task creation."""
    
    @patch('jamie.agent.controller.StreamingAgent')
    @patch('jamie.agent.controller.get_config')
    def test_stream_creates_background_task(self, mock_get_config, mock_agent_cls):
        """Start stream creates a background task for the agent."""
        from jamie.agent import controller
        controller._agents.clear()
        controller._agent_tasks.clear()
        controller._config = None
        
        mock_config = MagicMock()
        mock_config.discord_email.get_secret_value.return_value = "test@test.com"
        mock_config.discord_password.get_secret_value.return_value = "password"
        mock_config.model = "test-model"
        mock_config.max_budget_per_session = 2.0
        mock_config.sandbox_image = "test-image"
        mock_config.display_resolution = "1024x768"
        mock_get_config.return_value = mock_config
        
        mock_agent = AsyncMock()
        mock_agent_cls.return_value = mock_agent
        
        client = TestClient(controller.app)
        
        request = {
            "session_id": "task-test",
            "url": "https://test.com/video",
            "guild_id": "123",
            "channel_id": "456",
            "channel_name": "Test",
            "requester_id": "789"
        }
        
        response = client.post("/stream", json=request)
        assert response.status_code == 200
        
        # Verify agent's start method was called
        mock_agent.start.assert_called_once()
