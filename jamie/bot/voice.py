"""Voice channel detection for Jamie bot."""

from typing import Optional, Tuple
import discord

from jamie.shared.logging import get_logger

log = get_logger(__name__)


async def find_user_voice_channel(
    client: discord.Client,
    user: discord.User,
) -> Optional[discord.VoiceChannel]:
    """
    Find which voice channel a user is in across all shared guilds.
    
    Args:
        client: Discord client instance
        user: The user to find
        
    Returns:
        VoiceChannel if found, None otherwise
    """
    for guild in client.guilds:
        member = guild.get_member(user.id)
        if member and member.voice and member.voice.channel:
            log.debug(
                "user_found_in_voice",
                user_id=user.id,
                guild=guild.name,
                channel=member.voice.channel.name,
            )
            return member.voice.channel
    
    log.debug("user_not_in_voice", user_id=user.id)
    return None


async def find_user_voice_with_guild(
    client: discord.Client,
    user: discord.User,
) -> Tuple[Optional[discord.VoiceChannel], Optional[discord.Guild]]:
    """
    Find user's voice channel and guild.
    
    Returns:
        Tuple of (VoiceChannel, Guild) or (None, None)
    """
    for guild in client.guilds:
        member = guild.get_member(user.id)
        if member and member.voice and member.voice.channel:
            return member.voice.channel, guild
    
    return None, None


def get_voice_channel_info(channel: discord.VoiceChannel) -> dict:
    """Get info about a voice channel for logging/display."""
    return {
        "id": str(channel.id),
        "name": channel.name,
        "guild_id": str(channel.guild.id),
        "guild_name": channel.guild.name,
        "member_count": len(channel.members),
    }


async def is_user_in_channel(
    channel: discord.VoiceChannel,
    user_id: int,
) -> bool:
    """Check if a specific user is in a voice channel."""
    return any(m.id == user_id for m in channel.members)
