"""Session management for Jamie bot."""

from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio


class SessionState(str, Enum):
    """State of a bot-side streaming session."""
    CREATED = "created"
    REQUESTING = "requesting"
    ACTIVE = "active"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StreamSession:
    """Represents an active streaming session."""

    session_id: str
    requester_id: str
    guild_id: str
    channel_id: str
    channel_name: str
    url: str
    state: SessionState = SessionState.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    agent_status: Optional[str] = None

    @classmethod
    def create(
        cls,
        requester_id: str,
        guild_id: str,
        channel_id: str,
        channel_name: str,
        url: str,
    ) -> "StreamSession":
        """Create a new streaming session."""
        return cls(
            session_id=str(uuid.uuid4()),
            requester_id=requester_id,
            guild_id=guild_id,
            channel_id=channel_id,
            channel_name=channel_name,
            url=url,
        )

    def update_state(self, state: SessionState, error: Optional[str] = None) -> None:
        """Update session state."""
        self.state = state
        self.updated_at = datetime.utcnow()
        if error:
            self.error_message = error


class SessionManager:
    """Manages active streaming sessions.
    
    Thread-safe via asyncio.Lock. Enforces one stream per user.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, StreamSession] = {}
        self._user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        requester_id: str,
        guild_id: str,
        channel_id: str,
        channel_name: str,
        url: str,
    ) -> StreamSession:
        """Create and register a new session.
        
        Raises:
            ValueError: If user already has an active session.
        """
        async with self._lock:
            if requester_id in self._user_sessions:
                existing_id = self._user_sessions[requester_id]
                existing = self._sessions.get(existing_id)
                if existing and existing.state not in (
                    SessionState.COMPLETED,
                    SessionState.FAILED,
                ):
                    raise ValueError(
                        f"User {requester_id} already has an active session: {existing_id}"
                    )
                # Clean up stale mapping
                del self._user_sessions[requester_id]

            session = StreamSession.create(
                requester_id=requester_id,
                guild_id=guild_id,
                channel_id=channel_id,
                channel_name=channel_name,
                url=url,
            )
            self._sessions[session.session_id] = session
            self._user_sessions[requester_id] = session.session_id
            return session

    async def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get session by ID."""
        async with self._lock:
            return self._sessions.get(session_id)

    async def get_user_session(self, user_id: str) -> Optional[StreamSession]:
        """Get active session for a user."""
        async with self._lock:
            session_id = self._user_sessions.get(user_id)
            if session_id is None:
                return None
            session = self._sessions.get(session_id)
            # Clean up if session ended
            if session and session.state in (SessionState.COMPLETED, SessionState.FAILED):
                return None
            return session

    async def update_session(
        self,
        session_id: str,
        state: SessionState,
        error: Optional[str] = None,
        agent_status: Optional[str] = None,
    ) -> bool:
        """Update session state.
        
        Returns:
            True if session was found and updated, False otherwise.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.update_state(state, error)
            if agent_status is not None:
                session.agent_status = agent_status
            return True

    async def remove_session(self, session_id: str) -> bool:
        """Remove a completed/failed session.
        
        Returns:
            True if session was found and removed, False otherwise.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            # Remove from both mappings
            del self._sessions[session_id]
            if self._user_sessions.get(session.requester_id) == session_id:
                del self._user_sessions[session.requester_id]
            return True

    async def is_user_streaming(self, user_id: str) -> bool:
        """Check if user has an active session."""
        session = await self.get_user_session(user_id)
        return session is not None

    async def get_all_active_sessions(self) -> list[StreamSession]:
        """Get all sessions that are not completed or failed."""
        async with self._lock:
            return [
                s for s in self._sessions.values()
                if s.state not in (SessionState.COMPLETED, SessionState.FAILED)
            ]

    async def cleanup_stale_sessions(self, max_age_seconds: float = 3600) -> int:
        """Remove sessions that have been completed/failed for too long.
        
        Args:
            max_age_seconds: Maximum age for ended sessions before cleanup.
            
        Returns:
            Number of sessions cleaned up.
        """
        async with self._lock:
            now = datetime.utcnow()
            stale_ids = []
            for session_id, session in self._sessions.items():
                if session.state in (SessionState.COMPLETED, SessionState.FAILED):
                    age = (now - session.updated_at).total_seconds()
                    if age > max_age_seconds:
                        stale_ids.append(session_id)
            
            for session_id in stale_ids:
                session = self._sessions.pop(session_id)
                if self._user_sessions.get(session.requester_id) == session_id:
                    del self._user_sessions[session.requester_id]
            
            return len(stale_ids)
