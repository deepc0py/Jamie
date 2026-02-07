"""End-to-end integration tests for full Jamie flow.

Tests the complete stream lifecycle:
DM → bot → controller → agent → webhook → bot

Uses real HTTP between components but mocks:
- Discord client (no real Discord connection)
- CUA sandbox (no real browser automation)
"""

import asyncio
from datetime import datetime
from typing import Optional, List
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import aiohttp
from aiohttp import web

from jamie.shared.models import (
    StreamRequest,
    StreamResponse,
    StatusUpdate,
    StreamStatus,
)
from jamie.bot.webhook import WebhookReceiver
from jamie.bot.session import SessionManager, SessionState
from jamie.bot.cua_client import CUAClient, CUAClientConfig


# Port allocation helper
def _get_free_port() -> int:
    """Get a free port by binding to 0 and checking what we get."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class MockDiscordMessage:
    """Mock Discord message for testing."""
    
    def __init__(self, content: str, author_id: str = "123456789"):
        self.content = content
        self.author = MagicMock()
        self.author.id = int(author_id)
        self.channel = MagicMock()
        self.channel.__class__.__name__ = "DMChannel"
        self._replies: List[str] = []
    
    async def reply(self, content: str) -> None:
        """Track replies for assertions."""
        self._replies.append(content)


class MockDiscordBot:
    """Mock Discord bot for testing."""
    
    def __init__(self):
        self.user = MagicMock()
        self.user.id = 999888777
        self.guilds = []
        self._users: dict = {}
        self._sent_messages: List[str] = []
    
    def get_user(self, user_id: int):
        """Get a cached user."""
        return self._users.get(user_id)
    
    async def fetch_user(self, user_id: int):
        """Fetch a user by ID."""
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.send = AsyncMock(side_effect=lambda m: self._sent_messages.append(m))
        self._users[user_id] = mock_user
        return mock_user


class MockStreamingAgent:
    """Mock CUA streaming agent that simulates the agent workflow."""
    
    def __init__(self, context):
        self.context = context
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._status_sequence = [
            StreamStatus.STARTING,
            StreamStatus.LOGGING_IN,
            StreamStatus.JOINING_VOICE,
            StreamStatus.OPENING_URL,
            StreamStatus.SHARING_SCREEN,
            StreamStatus.STREAMING,
        ]
    
    async def start(self) -> None:
        """Simulate agent startup sequence."""
        self._running = True
        self._http_session = aiohttp.ClientSession()
        
        try:
            # Send status updates through the webhook
            for status in self._status_sequence:
                if not self._running:
                    break
                await self._send_status(status)
                await asyncio.sleep(0.05)  # Brief delay between status updates
            
            # Stay in streaming state until stopped
            while self._running:
                await asyncio.sleep(0.1)
                
        finally:
            if self._http_session:
                await self._http_session.close()
                self._http_session = None
    
    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        await self._send_status(StreamStatus.STOPPING)
        await self._send_status(StreamStatus.STOPPED)
    
    async def _send_status(self, status: StreamStatus, error: Optional[str] = None) -> None:
        """Send status update via webhook."""
        if not self.context.webhook_url or not self._http_session:
            return
        
        update = StatusUpdate(
            session_id=self.context.session_id,
            status=status,
            message=f"Agent status: {status.value}",
            error_code=error,
        )
        
        try:
            async with self._http_session.post(
                self.context.webhook_url,
                json=update.model_dump(mode="json"),
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                await resp.json()
        except Exception:
            pass  # Ignore webhook errors in tests


class MockController:
    """Mock CUA controller that runs as a real HTTP server."""
    
    def __init__(self, port: int = 18001):
        self.port = port
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._agents: dict = {}
        self._agent_tasks: dict = {}
    
    async def start(self) -> None:
        """Start the controller server."""
        self._app = web.Application()
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_post("/stream", self._handle_stream)
        self._app.router.add_post("/stop/{session_id}", self._handle_stop)
        self._app.router.add_get("/sessions", self._handle_sessions)
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        self._site = web.TCPSite(self._runner, "127.0.0.1", self.port)
        await self._site.start()
    
    async def stop(self) -> None:
        """Stop the controller server."""
        # Stop all agent tasks - copy keys to avoid modification during iteration
        task_ids = list(self._agent_tasks.keys())
        for task_id in task_ids:
            task = self._agent_tasks.get(task_id)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._agents.clear()
        self._agent_tasks.clear()
        
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            self._site = None
            self._app = None
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "version": "0.1.0",
            "active_sessions": len(self._agents),
        })
    
    async def _handle_stream(self, request: web.Request) -> web.Response:
        """Start stream endpoint."""
        data = await request.json()
        req = StreamRequest(**data)
        
        if req.session_id in self._agents:
            return web.json_response(
                {"detail": "Session already exists"},
                status=409,
            )
        
        # Create mock agent context
        from jamie.agent.streamer import AgentContext
        context = AgentContext(
            session_id=req.session_id,
            url=str(req.url),
            guild_id=req.guild_id,
            channel_id=req.channel_id,
            channel_name=req.channel_name,
            webhook_url=str(req.webhook_url) if req.webhook_url else None,
        )
        
        # Create and start mock agent
        agent = MockStreamingAgent(context)
        self._agents[req.session_id] = agent
        
        async def run_agent():
            try:
                await agent.start()
            except Exception:
                pass
            finally:
                self._agents.pop(req.session_id, None)
                self._agent_tasks.pop(req.session_id, None)
        
        task = asyncio.create_task(run_agent())
        self._agent_tasks[req.session_id] = task
        
        response = StreamResponse(
            session_id=req.session_id,
            status=StreamStatus.PENDING,
            message="Stream request accepted",
        )
        return web.json_response(response.model_dump(mode="json"))
    
    async def _handle_stop(self, request: web.Request) -> web.Response:
        """Stop stream endpoint."""
        session_id = request.match_info["session_id"]
        
        agent = self._agents.get(session_id)
        if not agent:
            return web.json_response(
                {"detail": "Session not found"},
                status=404,
            )
        
        await agent.stop()
        
        # Cancel task
        task = self._agent_tasks.get(session_id)
        if task and not task.done():
            task.cancel()
        
        # Cleanup
        self._agents.pop(session_id, None)
        self._agent_tasks.pop(session_id, None)
        
        response = StreamResponse(
            session_id=session_id,
            status=StreamStatus.STOPPED,
            message="Stream stopped",
        )
        return web.json_response(response.model_dump(mode="json"))
    
    async def _handle_sessions(self, request: web.Request) -> web.Response:
        """List sessions endpoint."""
        return web.json_response({
            "count": len(self._agents),
            "sessions": list(self._agents.keys()),
        })


@pytest.fixture
async def test_ports():
    """Allocate unique ports for this test."""
    webhook_port = _get_free_port()
    controller_port = _get_free_port()
    return {"webhook": webhook_port, "controller": controller_port}


@pytest.fixture
async def webhook_receiver(test_ports):
    """Create and start a webhook receiver."""
    received_updates: List[StatusUpdate] = []
    
    async def callback(update: StatusUpdate) -> None:
        received_updates.append(update)
    
    receiver = WebhookReceiver(
        host="127.0.0.1",
        port=test_ports["webhook"],
        callback=callback,
    )
    await receiver.start()
    
    # Attach the updates list and port for assertions
    receiver.received_updates = received_updates
    receiver.port = test_ports["webhook"]
    
    yield receiver
    
    await receiver.stop()


@pytest.fixture
async def mock_controller(test_ports):
    """Create and start a mock CUA controller."""
    controller = MockController(port=test_ports["controller"])
    await controller.start()
    controller.port = test_ports["controller"]
    yield controller
    await controller.stop()


@pytest.fixture
def cua_client(test_ports):
    """Create a CUA client pointing at the mock controller."""
    config = CUAClientConfig(
        base_url=f"http://127.0.0.1:{test_ports['controller']}",
        timeout=10,
        max_retries=1,
    )
    return CUAClient(config)


@pytest.fixture
def session_manager():
    """Create a fresh session manager."""
    return SessionManager()


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    return MockDiscordBot()


class TestE2EStreamLifecycle:
    """End-to-end tests for the complete stream lifecycle."""
    
    @pytest.mark.asyncio
    async def test_full_stream_flow(
        self,
        webhook_receiver,
        mock_controller,
        cua_client,
        session_manager,
        mock_bot,
    ):
        """Test complete flow: request → start → status updates → stop.
        
        Simulates:
        1. User DM with URL
        2. Bot creates session
        3. Bot calls CUA controller
        4. Agent sends status updates via webhook
        5. Bot receives updates
        6. User requests stop
        7. Stream stops gracefully
        """
        user_id = "123456789"
        url = "https://youtube.com/watch?v=test123"
        
        # Step 1: Create session (simulates bot handling DM)
        session = await session_manager.create_session(
            requester_id=user_id,
            guild_id="guild-001",
            channel_id="channel-001",
            channel_name="General",
            url=url,
        )
        
        assert session.state == SessionState.CREATED
        assert session.requester_id == user_id
        
        # Step 2: Build stream request (as bot would)
        webhook_url = f"http://127.0.0.1:{webhook_receiver.port}/webhook/status"
        stream_request = StreamRequest(
            session_id=session.session_id,
            url=url,
            guild_id="guild-001",
            channel_id="channel-001",
            channel_name="General",
            requester_id=user_id,
            webhook_url=webhook_url,
        )
        
        # Step 3: Call CUA controller to start stream
        async with cua_client:
            # Health check first
            health = await cua_client.health_check()
            assert health.status == "healthy"
            
            # Start stream
            response = await cua_client.start_stream(stream_request)
            assert response.session_id == session.session_id
            assert response.status == StreamStatus.PENDING
            
            # Update session state
            await session_manager.update_session(
                session.session_id,
                state=SessionState.REQUESTING,
            )
            
            # Step 4: Wait for status updates to arrive via webhook
            await asyncio.sleep(0.5)  # Allow agent to send updates
            
            # Verify we received status updates
            assert len(webhook_receiver.received_updates) > 0
            
            # Check that we received the expected status progression
            received_statuses = [u.status for u in webhook_receiver.received_updates]
            assert StreamStatus.STARTING in received_statuses
            assert StreamStatus.STREAMING in received_statuses
            
            # Step 5: Stop the stream
            stop_response = await cua_client.stop_stream(
                session.session_id,
                user_id,
            )
            assert stop_response.status == StreamStatus.STOPPED
            
            # Verify stopped status was sent
            await asyncio.sleep(0.1)
            final_statuses = [u.status for u in webhook_receiver.received_updates]
            assert StreamStatus.STOPPED in final_statuses
    
    @pytest.mark.asyncio
    async def test_webhook_updates_session_state(
        self,
        webhook_receiver,
        mock_controller,
        cua_client,
        session_manager,
    ):
        """Test that webhook updates properly update session state."""
        user_id = "user-webhook-test"
        
        # Track state changes via a callback that updates session
        async def update_session_callback(update: StatusUpdate) -> None:
            webhook_receiver.received_updates.append(update)
            
            # Map status to session state (as bot would)
            status_to_state = {
                StreamStatus.PENDING: SessionState.REQUESTING,
                StreamStatus.STARTING: SessionState.REQUESTING,
                StreamStatus.LOGGING_IN: SessionState.REQUESTING,
                StreamStatus.JOINING_VOICE: SessionState.REQUESTING,
                StreamStatus.OPENING_URL: SessionState.ACTIVE,
                StreamStatus.SHARING_SCREEN: SessionState.ACTIVE,
                StreamStatus.STREAMING: SessionState.ACTIVE,
                StreamStatus.STOPPING: SessionState.STOPPING,
                StreamStatus.STOPPED: SessionState.COMPLETED,
                StreamStatus.FAILED: SessionState.FAILED,
            }
            
            new_state = status_to_state.get(update.status, SessionState.ACTIVE)
            await session_manager.update_session(
                update.session_id,
                state=new_state,
            )
        
        # Replace callback
        webhook_receiver.set_callback(update_session_callback)
        
        # Create session
        session = await session_manager.create_session(
            requester_id=user_id,
            guild_id="guild-002",
            channel_id="channel-002",
            channel_name="Movie Night",
            url="https://twitch.tv/test",
        )
        
        # Start stream
        webhook_url = f"http://127.0.0.1:{webhook_receiver.port}/webhook/status"
        stream_request = StreamRequest(
            session_id=session.session_id,
            url="https://twitch.tv/test",
            guild_id="guild-002",
            channel_id="channel-002",
            channel_name="Movie Night",
            requester_id=user_id,
            webhook_url=webhook_url,
        )
        
        async with cua_client:
            await cua_client.start_stream(stream_request)
            
            # Wait for updates
            await asyncio.sleep(0.5)
            
            # Verify session state was updated
            updated_session = await session_manager.get_session(session.session_id)
            assert updated_session.state == SessionState.ACTIVE
            
            # Stop and verify final state
            await cua_client.stop_stream(session.session_id, user_id)
            await asyncio.sleep(0.1)
            
            final_session = await session_manager.get_session(session.session_id)
            assert final_session.state == SessionState.COMPLETED
    
    @pytest.mark.asyncio
    async def test_duplicate_session_rejected(
        self,
        webhook_receiver,
        mock_controller,
        cua_client,
        session_manager,
    ):
        """Test that duplicate session IDs are rejected by controller."""
        session_id = f"dup-test-{uuid.uuid4()}"
        
        request = StreamRequest(
            session_id=session_id,
            url="https://youtube.com/watch?v=test",
            guild_id="guild-003",
            channel_id="channel-003",
            channel_name="General",
            requester_id="user-dup-test",
            webhook_url=f"http://127.0.0.1:{webhook_receiver.port}/webhook/status",
        )
        
        async with cua_client:
            # First request succeeds
            response1 = await cua_client.start_stream(request)
            assert response1.status == StreamStatus.PENDING
            
            # Second request with same session_id fails
            from jamie.bot.cua_client import CUAClientError
            from jamie.shared.errors import ErrorCode
            
            with pytest.raises(CUAClientError) as exc_info:
                await cua_client.start_stream(request)
            
            assert exc_info.value.code == ErrorCode.ALREADY_STREAMING


class TestE2EErrorScenarios:
    """Test error scenarios in the E2E flow."""
    
    @pytest.mark.asyncio
    async def test_controller_unavailable(self, session_manager):
        """Test handling when CUA controller is unavailable."""
        # Point to a port with no server
        config = CUAClientConfig(
            base_url="http://127.0.0.1:19999",
            timeout=1,
            max_retries=1,
        )
        client = CUAClient(config)
        
        from jamie.bot.cua_client import CUAClientError
        
        async with client:
            with pytest.raises(CUAClientError):
                await client.health_check()
    
    @pytest.mark.asyncio
    async def test_stop_nonexistent_session(
        self,
        mock_controller,
        cua_client,
    ):
        """Test stopping a session that doesn't exist."""
        from jamie.bot.cua_client import CUAClientError
        
        async with cua_client:
            with pytest.raises(CUAClientError):
                await cua_client.stop_stream("nonexistent-session", "user-123")


class TestE2EHealthCheck:
    """Test health check integration."""
    
    @pytest.mark.asyncio
    async def test_controller_health_check(self, mock_controller, cua_client):
        """Test health check endpoint via CUA client."""
        async with cua_client:
            health = await cua_client.health_check()
            assert health.status == "healthy"
            assert health.active_sessions == 0
    
    @pytest.mark.asyncio
    async def test_webhook_receiver_health(self, webhook_receiver):
        """Test webhook receiver health endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://127.0.0.1:{webhook_receiver.port}/health"
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data["status"] == "healthy"


class TestE2ESessionCount:
    """Test session counting across components."""
    
    @pytest.mark.asyncio
    async def test_active_session_count(
        self,
        webhook_receiver,
        mock_controller,
        cua_client,
    ):
        """Test that active session count is tracked correctly."""
        async with cua_client:
            # Initially no sessions
            health = await cua_client.health_check()
            assert health.active_sessions == 0
            
            # Start first session
            req1 = StreamRequest(
                session_id="count-test-1",
                url="https://youtube.com/watch?v=1",
                guild_id="g1",
                channel_id="c1",
                channel_name="Ch1",
                requester_id="u1",
                webhook_url=f"http://127.0.0.1:{webhook_receiver.port}/webhook/status",
            )
            await cua_client.start_stream(req1)
            
            await asyncio.sleep(0.1)
            health = await cua_client.health_check()
            assert health.active_sessions == 1
            
            # Start second session
            req2 = StreamRequest(
                session_id="count-test-2",
                url="https://youtube.com/watch?v=2",
                guild_id="g2",
                channel_id="c2",
                channel_name="Ch2",
                requester_id="u2",
                webhook_url=f"http://127.0.0.1:{webhook_receiver.port}/webhook/status",
            )
            await cua_client.start_stream(req2)
            
            await asyncio.sleep(0.1)
            health = await cua_client.health_check()
            assert health.active_sessions == 2
            
            # Stop first session
            await cua_client.stop_stream("count-test-1", "u1")
            await asyncio.sleep(0.1)
            
            health = await cua_client.health_check()
            assert health.active_sessions == 1
            
            # Stop second session
            await cua_client.stop_stream("count-test-2", "u2")
            await asyncio.sleep(0.1)
            
            health = await cua_client.health_check()
            assert health.active_sessions == 0
