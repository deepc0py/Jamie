# Discord.py API Reference for Jamie Bot

> **Purpose:** Research notes for building a Discord bot that listens for DMs with URLs, detects user voice channel presence, and coordinates with a CUA agent to stream content.

## Table of Contents

1. [Bot Setup & Authentication](#1-bot-setup--authentication)
2. [Intents Configuration](#2-intents-configuration)
3. [DM Handling](#3-dm-handling)
4. [Voice Channel Detection](#4-voice-channel-detection)
5. [Presence & Status Detection](#5-presence--status-detection)
6. [Relevant Events](#6-relevant-events)
7. [Code Examples for Jamie](#7-code-examples-for-jamie)
8. [Limitations](#8-limitations)

---

## 1. Bot Setup & Authentication

### Creating a Bot Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Navigate to "Bot" tab, create a bot
4. Copy the bot token (keep secret!)
5. Enable required privileged intents (see section 2)

### Basic Bot Structure

```python
import discord
from discord.ext import commands

# Intents are REQUIRED in discord.py 2.0+
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.dm_messages = True      # Required for DM handling
intents.guilds = True           # Required for guild/voice channel info
intents.voice_states = True     # Required to detect voice channel presence

# Using Client directly
client = discord.Client(intents=intents)

# Or using Bot (recommended for commands)
bot = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Blocking call - must be last
client.run('YOUR_BOT_TOKEN')
```

### Authentication Methods

```python
# Method 1: client.run() - blocks, handles event loop
client.run('token')

# Method 2: async start() - for manual event loop control
async def main():
    await client.start('token')
    
asyncio.run(main())

# Method 3: login() + connect() - most control
await client.login('token')
await client.connect()
```

---

## 2. Intents Configuration

### Required Intents for Jamie

```python
intents = discord.Intents.default()

# CRITICAL - These are needed:
intents.message_content = True  # Read message content (PRIVILEGED)
intents.dm_messages = True      # Receive DM events
intents.guilds = True           # Access guild data
intents.voice_states = True     # Detect voice channel presence

# Optional but useful:
intents.members = True          # Full member info (PRIVILEGED)
intents.presences = True        # User status/activity (PRIVILEGED)
```

### Privileged Intents

**Must be enabled in Discord Developer Portal:**

1. **Message Content Intent** - Required to access `message.content`
2. **Server Members Intent** - Required for full member caching
3. **Presence Intent** - Required for `Member.status` and `Member.activity`

> ⚠️ Bots in 100+ servers need verification to use privileged intents.

---

## 3. DM Handling

### Detecting DMs vs Server Messages

```python
@client.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == client.user:
        return
    
    # Check if this is a DM
    if isinstance(message.channel, discord.DMChannel):
        # This is a direct message!
        await handle_dm(message)
    else:
        # This is a server/guild message
        pass

async def handle_dm(message):
    """Handle DM messages"""
    user = message.author
    content = message.content
    
    # Check for URLs
    import re
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, content)
    
    if urls:
        await message.channel.send(f"Found URL: {urls[0]}")
```

### Channel Types

```python
# DM Channel - 1-on-1 with bot
isinstance(message.channel, discord.DMChannel)

# Group DM Channel (rare for bots)
isinstance(message.channel, discord.GroupChannel)

# Guild Text Channel
isinstance(message.channel, discord.TextChannel)

# Alternative: Check guild attribute
if message.guild is None:
    # This is a DM (no guild = private)
    pass
```

### Sending DMs

```python
# Method 1: Reply in existing DM
await message.channel.send("Response")

# Method 2: Send DM to any user
user = client.get_user(user_id)
# or
user = await client.fetch_user(user_id)
dm_channel = await user.create_dm()
await dm_channel.send("Hello!")

# Method 3: Shorthand
await user.send("Hello!")
```

---

## 4. Voice Channel Detection

### The Key Pattern: `member.voice.channel`

```python
# Get a member's current voice channel
if member.voice and member.voice.channel:
    voice_channel = member.voice.channel
    print(f"{member.name} is in {voice_channel.name}")
else:
    print(f"{member.name} is not in a voice channel")
```

### VoiceState Class

`member.voice` returns a `VoiceState` object (or `None` if not in voice):

```python
class VoiceState:
    deaf: bool              # Server deafened
    mute: bool              # Server muted
    self_deaf: bool         # Self-deafened
    self_mute: bool         # Self-muted
    self_stream: bool       # Streaming (Go Live)
    self_video: bool        # Camera on
    suppress: bool          # Suppressed in stage
    requested_to_speak_at: datetime  # Stage channel request
    channel: Optional[VoiceChannel]  # Current voice channel
    session_id: str         # Voice session ID
```

### VoiceChannel Class

```python
class VoiceChannel:
    id: int                 # Channel snowflake ID
    name: str               # Channel name
    guild: Guild            # Parent guild
    members: List[Member]   # All members in this channel
    bitrate: int            # Audio bitrate
    user_limit: int         # Max users (0 = unlimited)
    rtc_region: Optional[str]  # Voice region
    
    # Methods
    async def connect() -> VoiceClient  # Join the channel
    async def edit(**kwargs)            # Modify channel
```

### Finding User's Voice Channel from DM

**The Challenge:** When receiving a DM, we only have a `User` object, not a `Member`. We need to search shared guilds.

```python
async def find_user_voice_channel(user: discord.User) -> Optional[discord.VoiceChannel]:
    """Find which voice channel a user is in across shared guilds."""
    
    for guild in client.guilds:
        member = guild.get_member(user.id)
        if member and member.voice and member.voice.channel:
            return member.voice.channel
    
    return None

# Usage in on_message
@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        voice_channel = await find_user_voice_channel(message.author)
        
        if voice_channel:
            await message.channel.send(
                f"You're in {voice_channel.name} on {voice_channel.guild.name}"
            )
        else:
            await message.channel.send("You're not in any voice channel I can see.")
```

### Getting All Members in a Voice Channel

```python
voice_channel = member.voice.channel
members_in_channel = voice_channel.members  # List[Member]

for m in members_in_channel:
    print(f"  - {m.display_name}")
```

---

## 5. Presence & Status Detection

### Member Status

```python
# Requires presences intent!
member.status  # Status enum: online, offline, idle, dnd, invisible

# Check specific status
if member.status == discord.Status.online:
    print("User is online")
elif member.status == discord.Status.idle:
    print("User is idle")
elif member.status == discord.Status.dnd:
    print("User is DND")
elif member.status == discord.Status.offline:
    print("User appears offline")
```

### Activity Detection

```python
# Single activity
member.activity  # BaseActivity or None

# All activities
member.activities  # Tuple of activities

# Check activity type
activity = member.activity
if isinstance(activity, discord.Game):
    print(f"Playing: {activity.name}")
elif isinstance(activity, discord.Streaming):
    print(f"Streaming: {activity.name} at {activity.url}")
elif isinstance(activity, discord.Spotify):
    print(f"Listening to: {activity.title}")
elif isinstance(activity, discord.CustomActivity):
    print(f"Custom status: {activity.name}")
```

---

## 6. Relevant Events

### Message Events

```python
@client.event
async def on_message(message: discord.Message):
    """Fired when a message is received (DM or server)."""
    pass

@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """Fired when a message is edited."""
    pass
```

### Voice State Events

```python
@client.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):
    """Fired when someone's voice state changes."""
    
    # Joined a voice channel
    if before.channel is None and after.channel is not None:
        print(f"{member.name} joined {after.channel.name}")
    
    # Left a voice channel
    elif before.channel is not None and after.channel is None:
        print(f"{member.name} left {before.channel.name}")
    
    # Moved between channels
    elif before.channel != after.channel:
        print(f"{member.name} moved from {before.channel.name} to {after.channel.name}")
    
    # Started streaming
    if not before.self_stream and after.self_stream:
        print(f"{member.name} started streaming in {after.channel.name}")
```

### Presence Events

```python
@client.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    """Fired when a member's presence changes (requires presences intent)."""
    
    if before.status != after.status:
        print(f"{after.name} changed status: {before.status} -> {after.status}")
```

### Lifecycle Events

```python
@client.event
async def on_ready():
    """Bot is connected and ready."""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print(f'Connected to {len(client.guilds)} guilds')

@client.event
async def on_connect():
    """Connected to Discord gateway (before caching)."""
    pass

@client.event  
async def on_disconnect():
    """Disconnected from Discord."""
    pass
```

---

## 7. Code Examples for Jamie

### Complete Jamie Bot Skeleton

```python
import discord
import re
import asyncio
from typing import Optional

class JamieBot(discord.Client):
    """Discord bot that receives URLs via DM and streams to voice channels."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guilds = True
        intents.voice_states = True
        intents.members = True  # Optional: for better member lookup
        
        super().__init__(intents=intents)
        
        self.url_pattern = re.compile(
            r'https?://(?:www\.)?'
            r'(?:youtube\.com/watch\?v=|youtu\.be/|twitch\.tv/|vimeo\.com/)'
            r'[\w\-]+'
        )
    
    async def on_ready(self):
        print(f'Jamie is online as {self.user}')
        print(f'Watching {len(self.guilds)} servers')
    
    async def on_message(self, message: discord.Message):
        # Ignore self
        if message.author == self.user:
            return
        
        # Only process DMs
        if not isinstance(message.channel, discord.DMChannel):
            return
        
        await self.handle_dm(message)
    
    async def handle_dm(self, message: discord.Message):
        """Process DM containing potential streaming URL."""
        user = message.author
        content = message.content
        
        # Extract URL
        match = self.url_pattern.search(content)
        if not match:
            await message.channel.send(
                "Send me a YouTube, Twitch, or Vimeo URL and I'll stream it!"
            )
            return
        
        url = match.group(0)
        
        # Find user's voice channel
        voice_channel = await self.find_user_voice_channel(user)
        
        if not voice_channel:
            await message.channel.send(
                "❌ You need to be in a voice channel first!\n"
                "Join a voice channel in any server we share, then try again."
            )
            return
        
        # Confirm and trigger streaming
        await message.channel.send(
            f"✅ Found you in **{voice_channel.name}** on **{voice_channel.guild.name}**\n"
            f"🎬 Queueing stream: {url}"
        )
        
        # Trigger CUA agent here
        await self.start_stream(url, voice_channel)
    
    async def find_user_voice_channel(
        self, 
        user: discord.User
    ) -> Optional[discord.VoiceChannel]:
        """Find user's current voice channel across all shared guilds."""
        
        for guild in self.guilds:
            member = guild.get_member(user.id)
            if member and member.voice and member.voice.channel:
                return member.voice.channel
        
        return None
    
    async def start_stream(
        self, 
        url: str, 
        voice_channel: discord.VoiceChannel
    ):
        """Trigger CUA agent to stream URL to the voice channel."""
        
        # TODO: Communicate with CUA agent
        # Options:
        # 1. HTTP request to CUA endpoint
        # 2. Message queue (Redis, RabbitMQ)
        # 3. Direct process invocation
        # 4. WebSocket connection
        
        guild_id = voice_channel.guild.id
        channel_id = voice_channel.id
        channel_name = voice_channel.name
        
        print(f"[STREAM REQUEST]")
        print(f"  URL: {url}")
        print(f"  Guild: {guild_id}")
        print(f"  Channel: {channel_id} ({channel_name})")
        
        # Example: Call external script
        # await self.run_cua_stream(url, guild_id, channel_id)

# Run the bot
if __name__ == '__main__':
    bot = JamieBot()
    bot.run('YOUR_BOT_TOKEN')
```

### Monitoring Voice Channel Changes

```python
@client.event
async def on_voice_state_update(member, before, after):
    """Track when users join/leave voice channels."""
    
    # User we're streaming to left the channel?
    if before.channel and not after.channel:
        if is_active_stream_channel(before.channel.id):
            # They left - maybe pause/stop stream?
            await handle_viewer_left(member, before.channel)
    
    # User joined a channel where we're streaming?
    if after.channel and not before.channel:
        if is_active_stream_channel(after.channel.id):
            await handle_viewer_joined(member, after.channel)
```

---

## 8. Limitations

### What discord.py CAN'T Do

1. **No Screen Sharing/Streaming API**
   - discord.py can JOIN voice channels but cannot stream video/screen
   - Discord's streaming is client-only, not exposed via bot API
   - **Workaround:** Use browser automation (Selenium/Playwright) with a real Discord client

2. **No Audio/Video Capture**
   - Bot can play audio files via `VoiceClient.play()`
   - Cannot capture or transmit video streams
   - **Workaround:** CUA agent with browser control

3. **Limited DM Context**
   - From a DM, you only get `User`, not `Member`
   - Must search shared guilds to find voice state
   - User must be in a guild the bot can see

4. **Rate Limits**
   - Gateway: 120 requests/60 seconds
   - REST API: Varies by endpoint
   - Member queries: Throttled

5. **Privileged Intents Requirements**
   - `message_content` - Required to read messages
   - `members` - Required for member caching
   - `presences` - Required for status/activity
   - Must be enabled in Developer Portal

6. **No "Go Live" Detection Initiation**
   - Can detect when someone starts streaming (`self_stream`)
   - Cannot programmatically start a stream

### The Streaming Problem & Solution

**Problem:** Discord bots cannot screen share or stream video.

**Solution for Jamie:**
1. **Jamie bot** (discord.py) handles:
   - Receiving DMs with URLs
   - Finding user's voice channel
   - Triggering the stream request

2. **CUA Agent** (browser automation) handles:
   - Opening Discord in a browser
   - Joining the voice channel
   - Screen sharing/streaming the content
   - Actual video playback

This hybrid approach lets us use discord.py for the bot logic while the CUA handles the browser-based streaming that bots can't do natively.

---

## Quick Reference

| Need | Solution |
|------|----------|
| Detect if message is DM | `isinstance(message.channel, discord.DMChannel)` |
| Get user's voice channel | `member.voice.channel` |
| Find member from user | `guild.get_member(user.id)` |
| Send DM | `await user.send("text")` |
| Check if streaming | `member.voice.self_stream` |
| Voice state changes | `on_voice_state_update(member, before, after)` |
| Required intents | `message_content`, `dm_messages`, `guilds`, `voice_states` |

---

*Last updated: 2026-02-07*
*Source: https://discordpy.readthedocs.io/en/stable/api.html*
