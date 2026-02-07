"""Centralized message templates for Jamie bot.

All user-facing messages in one place for consistency:
- Consistent emoji usage
- Friendly, helpful tone
- Clear error guidance
- Progress indicators
"""

from jamie.bot.session import SessionState


# =============================================================================
# Emoji Constants
# =============================================================================

class Emoji:
    """Consistent emoji usage across all messages."""
    
    # Status indicators
    MOVIE = "🎬"
    STOP = "🛑"
    CHECK = "✅"
    ERROR = "❌"
    LOADING = "⏳"
    NEW = "🆕"
    QUESTION = "❓"
    
    # Content types
    POPCORN = "🍿"
    LINK = "🔗"
    VOICE = "🎙️"
    HELP = "💡"
    
    # Status mapping for session states
    STATUS_MAP = {
        SessionState.CREATED: "🆕",
        SessionState.REQUESTING: "⏳",
        SessionState.ACTIVE: "🎬",
        SessionState.STOPPING: "🛑",
        SessionState.COMPLETED: "✅",
        SessionState.FAILED: "❌",
    }
    
    @classmethod
    def for_state(cls, state: SessionState) -> str:
        """Get emoji for a session state."""
        return cls.STATUS_MAP.get(state, cls.QUESTION)


# =============================================================================
# Help & Info Messages
# =============================================================================

HELP_MESSAGE = f"""{Emoji.MOVIE} **Jamie - Discord Stream Bot**

**How to use:**
1. Join a voice channel in a server where I'm a member
2. DM me a URL to stream
3. Sit back and enjoy! {Emoji.POPCORN}

**Supported services:**
• YouTube (videos, shorts, live)
• Twitch (channels)
• Vimeo
• Wikipedia
• Any other URL

**Commands:**
• `stop` - Stop your current stream
• `status` - Check your stream status
• `help` - Show this message

{Emoji.HELP} **Tip:** I work best with direct video URLs!"""


# =============================================================================
# Stream Lifecycle Messages
# =============================================================================

def stream_starting(service_name: str, channel_name: str, guild_name: str) -> str:
    """Message when stream request is acknowledged."""
    return (
        f"{Emoji.MOVIE} Starting **{service_name}** stream to "
        f"**{channel_name}** in {guild_name}...\n\n"
        f"{Emoji.HELP} *Tip: Send `stop` anytime to end the stream.*"
    )


def stream_active(channel_name: str) -> str:
    """Message when stream is confirmed active."""
    return (
        f"{Emoji.CHECK} Now streaming to **{channel_name}**!\n\n"
        f"{Emoji.POPCORN} Enjoy the show! Send `stop` when you're done."
    )


def stream_stopping() -> str:
    """Message when stop is acknowledged."""
    return f"{Emoji.STOP} Stopping your stream..."


def stream_stopped(channel_name: str) -> str:
    """Message when stream has fully stopped."""
    return (
        f"{Emoji.CHECK} Stream to **{channel_name}** ended.\n\n"
        "Send me another link anytime to start a new stream!"
    )


# =============================================================================
# Status Messages
# =============================================================================

def status_message(
    state: SessionState,
    channel_name: str,
    url: str,
    error_message: str | None = None,
) -> str:
    """Build a formatted status message."""
    emoji = Emoji.for_state(state)
    
    msg = (
        f"{emoji} **Stream Status**\n"
        f"• Channel: {channel_name}\n"
        f"• URL: {url}\n"
        f"• Status: {state.value}"
    )
    
    if error_message:
        msg += f"\n• Error: {error_message}"
    
    # Add contextual tips based on state
    if state == SessionState.ACTIVE:
        msg += f"\n\n{Emoji.HELP} *Send `stop` to end the stream.*"
    elif state == SessionState.FAILED:
        msg += f"\n\n{Emoji.HELP} *Try sending the URL again, or a different link.*"
    
    return msg


def no_active_stream() -> str:
    """Message when user has no active stream (for status/stop)."""
    return (
        f"{Emoji.QUESTION} You don't have an active stream.\n\n"
        "Send me a URL to start streaming!"
    )


# =============================================================================
# Error Messages
# =============================================================================

def error_stream_failed(error_msg: str) -> str:
    """Message when stream fails to start."""
    return (
        f"{Emoji.ERROR} **Failed to start stream**\n"
        f"Reason: {error_msg}\n\n"
        f"{Emoji.HELP} *Try again in a moment, or try a different URL.*"
    )


def error_stop_failed(error_msg: str) -> str:
    """Message when stop command fails."""
    return (
        f"{Emoji.ERROR} **Couldn't stop stream**\n"
        f"Reason: {error_msg}\n\n"
        f"{Emoji.HELP} *The stream may have already ended. Check `status` to confirm.*"
    )


def error_invalid_url(url: str) -> str:
    """Message when URL is invalid."""
    return (
        f"{Emoji.ERROR} That doesn't look like a valid URL:\n"
        f"`{url}`\n\n"
        f"{Emoji.HELP} *Make sure to include `https://` at the start.*"
    )


def error_no_url_found() -> str:
    """Message when no URL detected in message."""
    return (
        f"{Emoji.QUESTION} I didn't find a URL in your message.\n\n"
        f"Send me a link to stream, or type `help` for usage info."
    )


def error_not_in_voice() -> str:
    """Message when user isn't in a voice channel."""
    return (
        f"{Emoji.VOICE} You need to be in a voice channel!\n\n"
        "**How to fix:**\n"
        "1. Join a voice channel in a server where I'm a member\n"
        "2. Send me the URL again\n\n"
        f"{Emoji.HELP} *I'll stream directly to your voice channel.*"
    )


def error_already_streaming(channel_name: str) -> str:
    """Message when user already has an active stream."""
    return (
        f"{Emoji.MOVIE} You already have a stream running in **{channel_name}**!\n\n"
        "**Options:**\n"
        "• Send `stop` to end it first\n"
        "• Send `status` to check on it"
    )


def error_generic(error_msg: str) -> str:
    """Generic error message with guidance."""
    return (
        f"{Emoji.ERROR} Something went wrong: {error_msg}\n\n"
        f"{Emoji.HELP} *Try again, or type `help` if you're stuck.*"
    )
