"""DM message handler for Jamie bot."""

from typing import TYPE_CHECKING

import discord

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
            await message.reply("You don't have an active stream to stop.")
            return

        log.info("stop_requested", user_id=user_id, session_id=session.session_id)

        try:
            await self.cua_client.stop_stream(session.session_id, user_id)
            await self.session_manager.update_session(
                session.session_id,
                state=SessionState.STOPPING,
            )
            await message.reply("🛑 Stopping your stream...")
        except CUAClientError as e:
            log.error("stop_failed", user_id=user_id, error=str(e))
            await message.reply(f"Failed to stop stream: {e.message}")

    async def _handle_status(self, message: discord.Message) -> None:
        """Handle status command - show user's stream status."""
        user_id = str(message.author.id)
        
        session = await self.session_manager.get_user_session(user_id)
        if not session:
            await message.reply("You don't have an active stream.")
            return

        status_emoji = {
            SessionState.CREATED: "🆕",
            SessionState.REQUESTING: "⏳",
            SessionState.ACTIVE: "🎬",
            SessionState.STOPPING: "🛑",
            SessionState.COMPLETED: "✅",
            SessionState.FAILED: "❌",
        }
        
        emoji = status_emoji.get(session.state, "❓")
        status_msg = (
            f"{emoji} **Stream Status**\n"
            f"• Channel: {session.channel_name}\n"
            f"• URL: {session.url}\n"
            f"• Status: {session.state.value}"
        )
        
        if session.error_message:
            status_msg += f"\n• Error: {session.error_message}"
        
        await message.reply(status_msg)

    async def _handle_help(self, message: discord.Message) -> None:
        """Handle help command - show usage instructions."""
        help_text = (
            "🎬 **Jamie - Discord Stream Bot**\n\n"
            "**How to use:**\n"
            "1. Join a voice channel in a server where I'm a member\n"
            "2. DM me a URL to stream\n\n"
            "**Supported services:**\n"
            "• YouTube (videos, shorts, live)\n"
            "• Twitch (channels)\n"
            "• Vimeo\n"
            "• Wikipedia\n"
            "• Any other URL\n\n"
            "**Commands:**\n"
            "• `stop` - Stop your current stream\n"
            "• `status` - Check your stream status\n"
            "• `help` - Show this message"
        )
        await message.reply(help_text)

    async def _handle_url(self, message: discord.Message) -> None:
        """Handle URL message - start streaming if valid."""
        user_id = str(message.author.id)
        content = message.content.strip()

        # Extract URLs from message
        urls = extract_urls(content)
        if not urls:
            # No URL found - might be an unknown command
            await message.reply(
                "I didn't find a URL in your message. "
                "Send me a link to stream, or type `help` for usage."
            )
            return

        # Use the first URL found
        url = urls[0]
        parsed = parse_url(url)
        
        if not parsed:
            await message.reply(f"That doesn't look like a valid URL: {url}")
            return

        log.info(
            "stream_url_received",
            user_id=user_id,
            url=url,
            service=parsed.service.value,
        )

        # Check if user already has an active stream
        existing_session = await self.session_manager.get_user_session(user_id)
        if existing_session:
            await message.reply(
                f"You already have an active stream to **{existing_session.channel_name}**.\n"
                "Send `stop` to end it first, or `status` to check on it."
            )
            return

        # Find user's voice channel
        voice_channel, guild = await find_user_voice_with_guild(
            self.bot, message.author
        )

        if not voice_channel or not guild:
            await message.reply(
                "You need to be in a voice channel for me to stream there!\n"
                "Join a voice channel in a server where I'm a member, then send the URL again."
            )
            return

        # Create session
        try:
            session = await self.session_manager.create_session(
                requester_id=user_id,
                guild_id=str(guild.id),
                channel_id=str(voice_channel.id),
                channel_name=voice_channel.name,
                url=parsed.normalized or url,
            )
        except ValueError as e:
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
            url=parsed.normalized or url,
            guild_id=str(guild.id),
            channel_id=str(voice_channel.id),
            channel_name=voice_channel.name,
            requester_id=user_id,
            webhook_url=webhook_url,
        )

        # Send acknowledgment
        service_name = parsed.service.value.title()
        if parsed.service == StreamingService.GENERIC:
            service_name = "Link"

        await message.reply(
            f"🎬 Starting {service_name} stream to **{voice_channel.name}** in {guild.name}..."
        )

        # Request stream from CUA
        try:
            await self.session_manager.update_session(
                session.session_id,
                state=SessionState.REQUESTING,
            )
            
            response = await self.cua_client.start_stream(stream_request)
            
            log.info(
                "stream_requested",
                session_id=session.session_id,
                response_status=response.status.value,
            )
        except CUAClientError as e:
            log.error(
                "stream_request_failed",
                session_id=session.session_id,
                error=str(e),
            )
            await self.session_manager.update_session(
                session.session_id,
                state=SessionState.FAILED,
                error=e.message,
            )
            await message.channel.send(f"❌ Failed to start stream: {e.message}")
