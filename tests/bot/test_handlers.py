"""Unit tests for MessageHandler with mocked bot/client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from jamie.bot.handlers import MessageHandler
from jamie.bot.session import SessionManager, SessionState, StreamSession
from jamie.bot.cua_client import CUAClient, CUAClientError
from jamie.bot.url_patterns import StreamingService
from jamie.shared.errors import ErrorCode
from jamie.shared.models import StreamResponse, StreamStatus


class MockDiscordUser:
    """Mock Discord user for testing."""

    def __init__(self, user_id: int = 123456789):
        self.id = user_id
        self.name = "TestUser"
        self.mention = f"<@{user_id}>"


class MockDiscordMessage:
    """Mock Discord message for testing."""

    def __init__(
        self,
        content: str,
        author: MockDiscordUser = None,
        channel_type: str = "dm",
    ):
        self.content = content
        self.author = author or MockDiscordUser()
        self.reply = AsyncMock()
        
        if channel_type == "dm":
            self.channel = MagicMock(spec=discord.DMChannel)
        else:
            self.channel = MagicMock(spec=discord.TextChannel)
        
        self.channel.send = AsyncMock()


class MockVoiceChannel:
    """Mock Discord voice channel for testing."""

    def __init__(self, channel_id: int = 111222333, name: str = "General"):
        self.id = channel_id
        self.name = name
        self.members = []


class MockGuild:
    """Mock Discord guild for testing."""

    def __init__(self, guild_id: int = 987654321, name: str = "Test Server"):
        self.id = guild_id
        self.name = name


class MockJamieBot:
    """Mock JamieBot for testing."""

    def __init__(self):
        self.user = MockDiscordUser(user_id=999888777)
        self.config = MagicMock()
        self.config.webhook_host = "localhost"
        self.config.webhook_port = 5000
        self.guilds = []


@pytest.fixture
def mock_bot():
    """Create a mock JamieBot."""
    return MockJamieBot()


@pytest.fixture
def session_manager():
    """Create a fresh SessionManager."""
    return SessionManager()


@pytest.fixture
def mock_cua_client():
    """Create a mock CUAClient."""
    client = MagicMock(spec=CUAClient)
    client.start_stream = AsyncMock()
    client.stop_stream = AsyncMock()
    client.health_check = AsyncMock()
    return client


@pytest.fixture
def handler(mock_bot, session_manager, mock_cua_client):
    """Create a MessageHandler with mocked dependencies."""
    return MessageHandler(
        bot=mock_bot,
        session_manager=session_manager,
        cua_client=mock_cua_client,
    )


class TestMessageHandlerInit:
    """Tests for MessageHandler initialization."""

    def test_init_stores_dependencies(self, mock_bot, session_manager, mock_cua_client):
        """Handler should store bot, session_manager, and cua_client."""
        handler = MessageHandler(
            bot=mock_bot,
            session_manager=session_manager,
            cua_client=mock_cua_client,
        )
        
        assert handler.bot is mock_bot
        assert handler.session_manager is session_manager
        assert handler.cua_client is mock_cua_client


class TestHandleDMRouting:
    """Tests for handle_dm message routing."""

    @pytest.mark.asyncio
    async def test_ignores_self_messages(self, handler, mock_bot):
        """Handler should ignore messages from itself."""
        message = MockDiscordMessage(
            content="test",
            author=mock_bot.user,
        )
        
        await handler.handle_dm(message)
        
        # Should not reply to self
        message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_non_dm_messages(self, handler):
        """Handler should ignore non-DM messages."""
        message = MockDiscordMessage(
            content="test",
            channel_type="text",
        )
        
        await handler.handle_dm(message)
        
        # Should not process non-DM
        message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_routes_stop_command(self, handler):
        """Handler should route 'stop' to _handle_stop."""
        message = MockDiscordMessage(content="stop")
        
        with patch.object(handler, '_handle_stop', new_callable=AsyncMock) as mock_stop:
            await handler.handle_dm(message)
            mock_stop.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_routes_status_command(self, handler):
        """Handler should route 'status' to _handle_status."""
        message = MockDiscordMessage(content="status")
        
        with patch.object(handler, '_handle_status', new_callable=AsyncMock) as mock_status:
            await handler.handle_dm(message)
            mock_status.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_routes_help_command(self, handler):
        """Handler should route 'help' to _handle_help."""
        message = MockDiscordMessage(content="help")
        
        with patch.object(handler, '_handle_help', new_callable=AsyncMock) as mock_help:
            await handler.handle_dm(message)
            mock_help.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_routes_question_mark_to_help(self, handler):
        """Handler should route '?' to _handle_help."""
        message = MockDiscordMessage(content="?")
        
        with patch.object(handler, '_handle_help', new_callable=AsyncMock) as mock_help:
            await handler.handle_dm(message)
            mock_help.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_routes_url_to_handle_url(self, handler):
        """Handler should route URL messages to _handle_url."""
        message = MockDiscordMessage(content="https://youtube.com/watch?v=test123")
        
        with patch.object(handler, '_handle_url', new_callable=AsyncMock) as mock_url:
            await handler.handle_dm(message)
            mock_url.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_case_insensitive_commands(self, handler):
        """Commands should be case-insensitive."""
        for cmd in ["STOP", "Stop", "StOp"]:
            message = MockDiscordMessage(content=cmd)
            
            with patch.object(handler, '_handle_stop', new_callable=AsyncMock) as mock_stop:
                await handler.handle_dm(message)
                mock_stop.assert_called_once()


class TestHandleStop:
    """Tests for _handle_stop command."""

    @pytest.mark.asyncio
    async def test_stop_no_active_session(self, handler):
        """Stop with no active session should inform user."""
        message = MockDiscordMessage(content="stop")
        
        await handler._handle_stop(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "don't have an active stream" in reply_text

    @pytest.mark.asyncio
    async def test_stop_with_active_session(self, handler, session_manager, mock_cua_client):
        """Stop with active session should call CUA client."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="stop", author=user)
        
        # Create an active session
        session = await session_manager.create_session(
            requester_id=str(user.id),
            guild_id="guild123",
            channel_id="channel456",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        mock_cua_client.stop_stream.return_value = StreamResponse(
            session_id=session.session_id,
            status=StreamStatus.STOPPED,
            message="Stopped",
        )
        
        await handler._handle_stop(message)
        
        mock_cua_client.stop_stream.assert_called_once_with(
            session.session_id, str(user.id)
        )
        message.reply.assert_called_once()
        assert "Stopping" in message.reply.call_args[0][0]

    @pytest.mark.asyncio
    async def test_stop_cua_error(self, handler, session_manager, mock_cua_client):
        """Stop that fails should inform user of error."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="stop", author=user)
        
        # Create an active session
        await session_manager.create_session(
            requester_id=str(user.id),
            guild_id="guild123",
            channel_id="channel456",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        
        mock_cua_client.stop_stream.side_effect = CUAClientError(
            code=ErrorCode.CUA_UNAVAILABLE,
            message="Connection refused",
        )
        
        await handler._handle_stop(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "stop" in reply_text.lower() or "Connection refused" in reply_text


class TestHandleStatus:
    """Tests for _handle_status command."""

    @pytest.mark.asyncio
    async def test_status_no_active_session(self, handler):
        """Status with no active session should inform user."""
        message = MockDiscordMessage(content="status")
        
        await handler._handle_status(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "don't have an active stream" in reply_text

    @pytest.mark.asyncio
    async def test_status_with_active_session(self, handler, session_manager):
        """Status with active session should show details."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="status", author=user)
        
        # Create an active session
        session = await session_manager.create_session(
            requester_id=str(user.id),
            guild_id="guild123",
            channel_id="channel456",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        await session_manager.update_session(session.session_id, SessionState.ACTIVE)
        
        await handler._handle_status(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "General" in reply_text  # channel name
        assert "youtube.com" in reply_text  # URL
        assert "active" in reply_text  # state

    @pytest.mark.asyncio
    async def test_status_shows_error_message(self, handler, session_manager):
        """Status should show error message if present."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="status", author=user)
        
        session = await session_manager.create_session(
            requester_id=str(user.id),
            guild_id="guild123",
            channel_id="channel456",
            channel_name="General",
            url="https://youtube.com/watch?v=test",
        )
        await session_manager.update_session(
            session.session_id,
            SessionState.FAILED,
            error="Connection timeout",
        )
        
        # Need to make session still appear active for status
        # Failed sessions return None from get_user_session, so use REQUESTING instead
        session.state = SessionState.REQUESTING
        session.error_message = "Connection timeout"
        
        await handler._handle_status(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "Connection timeout" in reply_text


class TestHandleHelp:
    """Tests for _handle_help command."""

    @pytest.mark.asyncio
    async def test_help_shows_instructions(self, handler):
        """Help should show usage instructions."""
        message = MockDiscordMessage(content="help")
        
        await handler._handle_help(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "Jamie" in reply_text
        assert "YouTube" in reply_text
        assert "Twitch" in reply_text
        assert "stop" in reply_text
        assert "status" in reply_text


class TestHandleURL:
    """Tests for _handle_url and URL processing."""

    @pytest.mark.asyncio
    async def test_no_url_in_message(self, handler):
        """Message without URL should show help."""
        message = MockDiscordMessage(content="hello there")
        
        await handler._handle_url(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "didn't find a URL" in reply_text

    @pytest.mark.asyncio
    async def test_invalid_url_format(self, handler):
        """Invalid URL format should show error."""
        message = MockDiscordMessage(content="watch this: ftp://files.example.com")
        
        await handler._handle_url(message)
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "didn't find a URL" in reply_text

    @pytest.mark.asyncio
    async def test_valid_url_delegates_to_stream_request(self, handler):
        """Valid URL should delegate to _handle_stream_request."""
        message = MockDiscordMessage(content="https://youtube.com/watch?v=dQw4w9WgXcQ")
        
        with patch.object(
            handler, '_handle_stream_request', new_callable=AsyncMock
        ) as mock_stream:
            await handler._handle_url(message)
            
            mock_stream.assert_called_once()
            call_kwargs = mock_stream.call_args[1]
            assert call_kwargs['message'] is message
            assert "youtube.com" in call_kwargs['url']
            assert call_kwargs['service'] == StreamingService.YOUTUBE


class TestHandleStreamRequest:
    """Tests for _handle_stream_request orchestration."""

    @pytest.mark.asyncio
    async def test_user_already_streaming(self, handler, session_manager):
        """User with active session should be blocked."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="https://youtube.com/watch?v=test", author=user)
        
        # Create existing session
        await session_manager.create_session(
            requester_id=str(user.id),
            guild_id="guild123",
            channel_id="channel456",
            channel_name="General",
            url="https://youtube.com/watch?v=existing",
        )
        
        await handler._handle_stream_request(
            message=message,
            user_id=str(user.id),
            url="https://youtube.com/watch?v=test",
            service=StreamingService.YOUTUBE,
        )
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "already have" in reply_text.lower() or "stream running" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_user_not_in_voice_channel(self, handler):
        """User not in voice channel should be blocked."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="https://youtube.com/watch?v=test", author=user)
        
        with patch(
            'jamie.bot.handlers.find_user_voice_with_guild',
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            await handler._handle_stream_request(
                message=message,
                user_id=str(user.id),
                url="https://youtube.com/watch?v=test",
                service=StreamingService.YOUTUBE,
            )
        
        message.reply.assert_called_once()
        reply_text = message.reply.call_args[0][0]
        assert "need to be in a voice channel" in reply_text

    @pytest.mark.asyncio
    async def test_successful_stream_request(self, handler, mock_cua_client):
        """Successful stream request should call CUA and acknowledge."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="https://youtube.com/watch?v=test", author=user)
        
        mock_voice = MockVoiceChannel()
        mock_guild = MockGuild()
        
        mock_cua_client.start_stream.return_value = StreamResponse(
            session_id="new-session-123",
            status=StreamStatus.PENDING,
            message="Request accepted",
        )
        
        with patch(
            'jamie.bot.handlers.find_user_voice_with_guild',
            new_callable=AsyncMock,
            return_value=(mock_voice, mock_guild),
        ):
            await handler._handle_stream_request(
                message=message,
                user_id=str(user.id),
                url="https://www.youtube.com/watch?v=test",
                service=StreamingService.YOUTUBE,
            )
        
        # Should acknowledge the request
        message.reply.assert_called()
        reply_text = message.reply.call_args[0][0]
        assert "Starting" in reply_text
        assert "youtube" in reply_text.lower()
        
        # Should call CUA
        mock_cua_client.start_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_cua_error_marks_session_failed(self, handler, session_manager, mock_cua_client):
        """CUA error should mark session as failed."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="https://youtube.com/watch?v=test", author=user)
        
        mock_voice = MockVoiceChannel()
        mock_guild = MockGuild()
        
        mock_cua_client.start_stream.side_effect = CUAClientError(
            code=ErrorCode.CUA_UNAVAILABLE,
            message="CUA is down",
        )
        
        with patch(
            'jamie.bot.handlers.find_user_voice_with_guild',
            new_callable=AsyncMock,
            return_value=(mock_voice, mock_guild),
        ):
            await handler._handle_stream_request(
                message=message,
                user_id=str(user.id),
                url="https://www.youtube.com/watch?v=test",
                service=StreamingService.YOUTUBE,
            )
        
        # Should send error message
        message.channel.send.assert_called()
        send_text = message.channel.send.call_args[0][0]
        assert "Failed" in send_text

    @pytest.mark.asyncio
    async def test_generic_service_name(self, handler, mock_cua_client):
        """Generic URLs should show 'Link' instead of service name."""
        user = MockDiscordUser(user_id=123456789)
        message = MockDiscordMessage(content="https://example.com/video", author=user)
        
        mock_voice = MockVoiceChannel()
        mock_guild = MockGuild()
        
        mock_cua_client.start_stream.return_value = StreamResponse(
            session_id="new-session-123",
            status=StreamStatus.PENDING,
            message="Request accepted",
        )
        
        with patch(
            'jamie.bot.handlers.find_user_voice_with_guild',
            new_callable=AsyncMock,
            return_value=(mock_voice, mock_guild),
        ):
            await handler._handle_stream_request(
                message=message,
                user_id=str(user.id),
                url="https://example.com/video",
                service=StreamingService.GENERIC,
            )
        
        message.reply.assert_called()
        reply_text = message.reply.call_args[0][0]
        assert "Link" in reply_text


class TestIntegration:
    """Integration tests for full message handling flow."""

    @pytest.mark.asyncio
    async def test_full_stream_flow(self, handler, session_manager, mock_cua_client):
        """Test complete flow: URL -> stream -> status -> stop."""
        user = MockDiscordUser(user_id=123456789)
        mock_voice = MockVoiceChannel()
        mock_guild = MockGuild()
        
        # Configure CUA mock
        mock_cua_client.start_stream.return_value = StreamResponse(
            session_id="session-abc",
            status=StreamStatus.PENDING,
            message="Starting",
        )
        mock_cua_client.stop_stream.return_value = StreamResponse(
            session_id="session-abc",
            status=StreamStatus.STOPPED,
            message="Stopped",
        )
        
        # 1. Send URL
        url_message = MockDiscordMessage(
            content="https://youtube.com/watch?v=dQw4w9WgXcQ",
            author=user,
        )
        
        with patch(
            'jamie.bot.handlers.find_user_voice_with_guild',
            new_callable=AsyncMock,
            return_value=(mock_voice, mock_guild),
        ):
            await handler.handle_dm(url_message)
        
        # Should have created a session
        session = await session_manager.get_user_session(str(user.id))
        assert session is not None
        
        # 2. Check status
        await session_manager.update_session(session.session_id, SessionState.ACTIVE)
        status_message = MockDiscordMessage(content="status", author=user)
        await handler.handle_dm(status_message)
        
        status_reply = status_message.reply.call_args[0][0]
        assert "active" in status_reply
        
        # 3. Stop stream
        stop_message = MockDiscordMessage(content="stop", author=user)
        await handler.handle_dm(stop_message)
        
        mock_cua_client.stop_stream.assert_called_once()
