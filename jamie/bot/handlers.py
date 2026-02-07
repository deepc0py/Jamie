"""DM message handler for Jamie bot."""

from typing import TYPE_CHECKING

import discord

from jamie.bot import messages as msg
from jamie.bot.session import SessionManager, SessionState
from jamie.bot.cua_client import CUAClient, CUAClientError
from jamie.bot.url_patterns import extract_urls, parse_url, StreamingService
from jamie.bot.voice import find_user_voice_with_guild
from jamie.shared.logging import get_logger
from jamie.shared.models import StreamRequest

if TYPE_CHECKING:
    from jamie.bot.bot import JamieBot

log = get_logger(__name__)


class MessageHandler:
    """Handles DM messages and routes to appropriate handlers."""

    def __init__(
        self,
        bot: "JamieBot",
        session_manager: SessionManager,
        cua_client: CUAClient,
    ):
        self.bot = bot
        self.session_manager = session_manager
        self.cua_client = cua_client

    async def handle_dm(self, message: discord.Message) -> None:
        """
        Handle an incoming DM message.
        
        Routes to:
        - stop: Stop active stream
        - status: Check stream status
        - help: Show usage info
        - URL: Start streaming
        """
        # Ignore messages from self
        if message.author == self.bot.user:
            return

        # Only process DMs
        if not isinstance(message.channel, discord.DMChannel):
            return

        content = message.content.strip().lower()
        user_id = str(message.author.id)

        log.debug(
            "dm_received",
            user_id=user_id,
            content_preview=content[:50] if content else "(empty)",
        )

        # Route to command handlers
        if content == "stop":
            await self._handle_stop(message)
        elif content == "status":
            await self._handle_status(message)
        elif content in ("help", "?"):
            await self._handle_help(message)
        else:
            # Check for URLs
            await self._handle_url(message)

    async def _handle_stop(self, message: discord.Message) -> None:
        """Handle stop command - stop user's active stream."""
        user_id = str(message.author.id)
        
        session = await self.session_manager.get_user_session(user_id)
        if not session:
            await message.reply(msg.no_active_stream())
            return

        log.info("stop_requested", user_id=user_id, session_id=session.session_id)

        try:
            await self.cua_client.stop_stream(session.session_id, user_id)
            await self.session_manager.update_session(
                session.session_id,
                state=SessionState.STOPPING,
            )
            await message.reply(msg.stream_stopping())
        except CUAClientError as e:
            log.error("stop_failed", user_id=user_id, error=str(e))
            await message.reply(msg.error_stop_failed(e.message))

    async def _handle_status(self, message: discord.Message) -> None:
        """Handle status command - show user's stream status."""
        user_id = str(message.author.id)
        
        session = await self.session_manager.get_user_session(user_id)
        if not session:
            await message.reply(msg.no_active_stream())
            return

        await message.reply(
            msg.status_message(
                state=session.state,
                channel_name=session.channel_name,
                url=session.url,
                error_message=session.error_message,
            )
        )

    async def _handle_help(self, message: discord.Message) -> None:
        """Handle help command - show usage instructions."""
        await message.reply(msg.HELP_MESSAGE)

    async def _handle_url(self, message: discord.Message) -> None:
        """Handle URL message - start streaming if valid."""
        user_id = str(message.author.id)
        content = message.content.strip()

        # Extract URLs from message
        urls = extract_urls(content)
        if not urls:
            # No URL found - might be an unknown command
            await message.reply(msg.error_no_url_found())
            return

        # Use the first URL found
        url = urls[0]
        parsed = parse_url(url)
        
        if not parsed:
            await message.reply(msg.error_invalid_url(url))
            return

        log.info(
            "stream_url_received",
            user_id=user_id,
            url=url,
            service=parsed.service.value,
        )

        # Delegate to stream request handler
        await self._handle_stream_request(
            message=message,
            user_id=user_id,
            url=parsed.normalized or url,
            service=parsed.service,
        )

    async def _handle_stream_request(
        self,
        message: discord.Message,
        user_id: str,
        url: str,
        service: StreamingService,
    ) -> None:
        """Handle stream request after URL validation.
        
        Orchestrates the full stream request flow:
        1. Check if user is already streaming (busy check)
        2. Find user's voice channel
        3. Create session via session_manager
        4. Call CUA client to start stream
        5. Handle response/errors with appropriate user messages
        6. Update session state based on CUA response
        
        Args:
            message: Discord message that triggered the request
            user_id: ID of the requesting user
            url: Normalized URL to stream
            service: Detected streaming service type
        """
        # Check if user already has an active stream
        existing_session = await self.session_manager.get_user_session(user_id)
        if existing_session:
            await message.reply(msg.error_already_streaming(existing_session.channel_name))
            return

        # Find user's voice channel
        voice_channel, guild = await find_user_voice_with_guild(
            self.bot, message.author
        )

        if not voice_channel or not guild:
            await message.reply(msg.error_not_in_voice())
            return

        # Create session via session_manager
        try:
            session = await self.session_manager.create_session(
                requester_id=user_id,
                guild_id=str(guild.id),
                channel_id=str(voice_channel.id),
                channel_name=voice_channel.name,
                url=url,
            )
        except ValueError as e:
            log.warning("session_create_failed", user_id=user_id, error=str(e))
            await message.reply(str(e))
            return

        log.info(
            "session_created",
            session_id=session.session_id,
            user_id=user_id,
            channel=voice_channel.name,
            guild=guild.name,
        )

        # Build webhook URL for status updates
        webhook_url = (
            f"http://{self.bot.config.webhook_host}:{self.bot.config.webhook_port}/status"
        )

        # Create stream request
        stream_request = StreamRequest(
            session_id=session.session_id,
            url=url,
            guild_id=str(guild.id),
            channel_id=str(voice_channel.id),
            channel_name=voice_channel.name,
            requester_id=user_id,
            webhook_url=webhook_url,
        )

        # Send acknowledgment
        service_name = service.value.title()
        if service == StreamingService.GENERIC:
            service_name = "Link"

        await message.reply(
            msg.stream_starting(service_name, voice_channel.name, guild.name)
        )

        # Call CUA client to start stream
        try:
            await self.session_manager.update_session(
                session.session_id,
                state=SessionState.REQUESTING,
            )
            
            response = await self.cua_client.start_stream(stream_request)
            
            # Update session state based on CUA response
            log.info(
                "stream_requested",
                session_id=session.session_id,
                response_status=response.status.value,
                message=response.message,
            )
            
            # Session will be updated to ACTIVE via webhook when CUA confirms streaming
            
        except CUAClientError as e:
            # Handle CUA errors with appropriate user messages
            log.error(
                "stream_request_failed",
                session_id=session.session_id,
                error=str(e),
                error_code=e.code.value if hasattr(e, 'code') else None,
            )
            await self.session_manager.update_session(
                session.session_id,
                state=SessionState.FAILED,
                error=e.message,
            )
            await message.channel.send(msg.error_stream_failed(e.message))
