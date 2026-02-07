"""Unit tests for SessionManager."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from jamie.bot.session import SessionManager, SessionState, StreamSession


class TestStreamSession:
    """Tests for StreamSession dataclass."""

    def test_create_generates_uuid(self):
        """StreamSession.create should generate a unique session_id."""
        session = StreamSession.create(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID format
        assert session.requester_id == "user123"
        assert session.guild_id == "guild456"
        assert session.channel_id == "channel789"
        assert session.channel_name == "General"
        assert session.url == "https://youtube.com/watch?v=test"
        assert session.state == SessionState.CREATED

    def test_create_sets_timestamps(self):
        """StreamSession.create should set created_at and updated_at."""
        before = datetime.utcnow()
        session = StreamSession.create(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://example.com",
        )
        after = datetime.utcnow()
        
        assert before <= session.created_at <= after
        assert before <= session.updated_at <= after

    def test_update_state_changes_state(self):
        """update_state should change the session state."""
        session = StreamSession.create(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://example.com",
        )
        
        old_updated = session.updated_at
        session.update_state(SessionState.ACTIVE)
        
        assert session.state == SessionState.ACTIVE
        assert session.updated_at >= old_updated

    def test_update_state_with_error(self):
        """update_state should set error_message when provided."""
        session = StreamSession.create(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://example.com",
        )
        
        session.update_state(SessionState.FAILED, error="Connection timeout")
        
        assert session.state == SessionState.FAILED
        assert session.error_message == "Connection timeout"


class TestSessionState:
    """Tests for SessionState enum."""

    def test_all_states_exist(self):
        """Verify all expected session states exist."""
        assert SessionState.CREATED == "created"
        assert SessionState.REQUESTING == "requesting"
        assert SessionState.ACTIVE == "active"
        assert SessionState.STOPPING == "stopping"
        assert SessionState.COMPLETED == "completed"
        assert SessionState.FAILED == "failed"

    def test_states_are_strings(self):
        """Session states should be string-valued."""
        for state in SessionState:
            assert isinstance(state.value, str)


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh SessionManager for each test."""
        return SessionManager()

    @pytest.mark.asyncio
    async def test_create_session_success(self, manager):
        """create_session should create and register a new session."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        assert session.session_id is not None
        assert session.requester_id == "user123"
        assert session.state == SessionState.CREATED
        
        # Verify it's retrievable
        retrieved = await manager.get_session(session.session_id)
        assert retrieved is session

    @pytest.mark.asyncio
    async def test_create_session_duplicate_user_raises(self, manager):
        """create_session should raise if user already has active session."""
        await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        with pytest.raises(ValueError, match="already has an active session"):
            await manager.create_session(
                requester_id="user123",
                guild_id="guild456",
                channel_id="channel000",
                channel_name="Other Channel",
                url="https://youtube.com/watch?v=other",
            )

    @pytest.mark.asyncio
    async def test_create_session_after_completed_allowed(self, manager):
        """create_session should allow new session after previous completed."""
        session1 = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        # Complete the first session
        await manager.update_session(session1.session_id, SessionState.COMPLETED)
        
        # Now should be able to create a new one
        session2 = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=other",
        )
        
        assert session2.session_id != session1.session_id

    @pytest.mark.asyncio
    async def test_create_session_after_failed_allowed(self, manager):
        """create_session should allow new session after previous failed."""
        session1 = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        # Fail the first session
        await manager.update_session(session1.session_id, SessionState.FAILED, error="test error")
        
        # Now should be able to create a new one
        session2 = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=other",
        )
        
        assert session2.session_id != session1.session_id

    @pytest.mark.asyncio
    async def test_get_session_returns_none_for_unknown(self, manager):
        """get_session should return None for unknown session_id."""
        result = await manager.get_session("unknown-session-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_session_returns_active(self, manager):
        """get_user_session should return user's active session."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        result = await manager.get_user_session("user123")
        assert result is session

    @pytest.mark.asyncio
    async def test_get_user_session_returns_none_for_unknown(self, manager):
        """get_user_session should return None for unknown user."""
        result = await manager.get_user_session("unknown-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_session_returns_none_for_completed(self, manager):
        """get_user_session should return None if session completed."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        await manager.update_session(session.session_id, SessionState.COMPLETED)
        
        result = await manager.get_user_session("user123")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_session_success(self, manager):
        """update_session should update state and return True."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        result = await manager.update_session(session.session_id, SessionState.ACTIVE)
        
        assert result is True
        retrieved = await manager.get_session(session.session_id)
        assert retrieved.state == SessionState.ACTIVE

    @pytest.mark.asyncio
    async def test_update_session_with_error(self, manager):
        """update_session should set error message."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        await manager.update_session(
            session.session_id,
            SessionState.FAILED,
            error="Something went wrong",
        )
        
        retrieved = await manager.get_session(session.session_id)
        assert retrieved.error_message == "Something went wrong"

    @pytest.mark.asyncio
    async def test_update_session_with_agent_status(self, manager):
        """update_session should set agent_status when provided."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        await manager.update_session(
            session.session_id,
            SessionState.ACTIVE,
            agent_status="streaming",
        )
        
        retrieved = await manager.get_session(session.session_id)
        assert retrieved.agent_status == "streaming"

    @pytest.mark.asyncio
    async def test_update_session_unknown_returns_false(self, manager):
        """update_session should return False for unknown session."""
        result = await manager.update_session("unknown-id", SessionState.ACTIVE)
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_session_success(self, manager):
        """remove_session should remove session and return True."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        result = await manager.remove_session(session.session_id)
        
        assert result is True
        assert await manager.get_session(session.session_id) is None
        assert await manager.get_user_session("user123") is None

    @pytest.mark.asyncio
    async def test_remove_session_unknown_returns_false(self, manager):
        """remove_session should return False for unknown session."""
        result = await manager.remove_session("unknown-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_user_streaming_true(self, manager):
        """is_user_streaming should return True for active user."""
        await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        result = await manager.is_user_streaming("user123")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_user_streaming_false(self, manager):
        """is_user_streaming should return False for unknown user."""
        result = await manager.is_user_streaming("unknown-user")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_active_sessions(self, manager):
        """get_all_active_sessions should return only active sessions."""
        session1 = await manager.create_session(
            requester_id="user1",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test1",
        )
        session2 = await manager.create_session(
            requester_id="user2",
            guild_id="guild456",
            channel_id="channel000",
            channel_name="Other",
            url="https://youtube.com/watch?v=test2",
        )
        # Mark session1 as completed
        await manager.update_session(session1.session_id, SessionState.COMPLETED)
        
        active = await manager.get_all_active_sessions()
        
        assert len(active) == 1
        assert active[0].session_id == session2.session_id

    @pytest.mark.asyncio
    async def test_cleanup_stale_sessions(self, manager):
        """cleanup_stale_sessions should remove old completed sessions."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        await manager.update_session(session.session_id, SessionState.COMPLETED)
        
        # Manually backdate the updated_at
        stored = await manager.get_session(session.session_id)
        stored.updated_at = datetime.utcnow() - timedelta(hours=2)
        
        # Cleanup with 1 hour max age
        count = await manager.cleanup_stale_sessions(max_age_seconds=3600)
        
        assert count == 1
        assert await manager.get_session(session.session_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_stale_sessions_keeps_recent(self, manager):
        """cleanup_stale_sessions should keep recent completed sessions."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        await manager.update_session(session.session_id, SessionState.COMPLETED)
        
        # Don't backdate, should not be cleaned up
        count = await manager.cleanup_stale_sessions(max_age_seconds=3600)
        
        assert count == 0
        assert await manager.get_session(session.session_id) is not None

    @pytest.mark.asyncio
    async def test_cleanup_stale_sessions_keeps_active(self, manager):
        """cleanup_stale_sessions should not remove active sessions."""
        session = await manager.create_session(
            requester_id="user123",
            guild_id="guild456",
            channel_id="channel789",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        await manager.update_session(session.session_id, SessionState.ACTIVE)
        
        # Even if we backdate
        stored = await manager.get_session(session.session_id)
        stored.updated_at = datetime.utcnow() - timedelta(hours=2)
        
        count = await manager.cleanup_stale_sessions(max_age_seconds=3600)
        
        assert count == 0
        assert await manager.get_session(session.session_id) is not None
