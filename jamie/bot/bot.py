"""Main Jamie Discord bot class."""

from typing import Optional, TYPE_CHECKING

import discord
from discord.ext import commands

from jamie.bot.session import SessionManager, SessionState
from jamie.bot.cua_client import CUAClient
from jamie.bot.webhook import WebhookReceiver
from jamie.shared.config import BotConfig, get_bot_config
from jamie.shared.logging import get_logger, bind_context
from jamie.shared.models import StatusUpdate, StreamStatus

if TYPE_CHECKING:
    from jamie.bot.handlers import MessageHandler

log = get_logger(__name__)


# Map agent StreamStatus to bot SessionState
STATUS_TO_STATE = {
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


class JamieBot(commands.Bot):
    """Discord bot for streaming URLs to voice channels."""

    def __init__(self, config: Optional[BotConfig] = None):
        self.config = config or get_bot_config()

        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guilds = True
        intents.voice_states = True

        super().__init__(
            command_prefix="!",  # Not used, we handle DMs
            intents=intents,
        )

        # Components
        self.session_manager = SessionManager()
        self.cua_client = CUAClient()
        self.webhook_receiver: Optional[WebhookReceiver] = None
        self.message_handler: Optional["MessageHandler"] = None

    async def setup_hook(self) -> None:
        """Called when bot is starting up."""
        log.info("bot_starting")

        # Start webhook receiver
        self.webhook_receiver = WebhookReceiver(
            host=self.config.webhook_host,
            port=self.config.webhook_port,
            callback=self._handle_status_update,
        )
        await self.webhook_receiver.start()

        # Initialize message handler (import here to avoid circular imports)
        try:
            from jamie.bot.handlers import MessageHandler

            self.message_handler = MessageHandler(
                bot=self,
                session_manager=self.session_manager,
                cua_client=self.cua_client,
            )
        except ImportError:
            log.warning("message_handler_unavailable")
            self.message_handler = None

    async def on_ready(self) -> None:
        """Called when bot is connected and ready."""
        log.info(
            "bot_ready",
            user=str(self.user),
            guilds=len(self.guilds),
        )

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        # Ignore our own messages
        if message.author == self.user:
            return

        # Only handle DMs
        if not isinstance(message.channel, discord.DMChannel):
            return

        bind_context(user_id=str(message.author.id))

        if self.message_handler:
            await self.message_handler.handle_dm(message)

    async def _handle_status_update(self, update: StatusUpdate) -> None:
        """Handle status update from CUA agent."""
        session = await self.session_manager.get_session(update.session_id)
        if not session:
            log.warning("status_update_unknown_session", session_id=update.session_id)
            return

        # Map agent status to session state
        new_state = STATUS_TO_STATE.get(update.status, SessionState.ACTIVE)

        # Update session state
        await self.session_manager.update_session(
            update.session_id,
            state=new_state,
            error=update.error_code,
            agent_status=update.status.value,
        )

        # Notify user
        try:
            user = self.get_user(int(session.requester_id))
            if user is None:
                user = await self.fetch_user(int(session.requester_id))
            if user:
                await user.send(f"🎬 Stream status: {update.status.value}")
        except discord.NotFound:
            log.warning("user_not_found", user_id=session.requester_id)
        except discord.Forbidden:
            log.warning("cannot_dm_user", user_id=session.requester_id)

    async def close(self) -> None:
        """Clean shutdown."""
        log.info("bot_stopping")

        if self.webhook_receiver:
            await self.webhook_receiver.stop()

        await self.cua_client.close()
        await super().close()


def create_bot(config: Optional[BotConfig] = None) -> JamieBot:
    """Factory function to create bot instance."""
    return JamieBot(config)
