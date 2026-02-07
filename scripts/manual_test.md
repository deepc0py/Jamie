# Jamie Manual End-to-End Test

This document provides a step-by-step checklist for manually testing Jamie's complete streaming workflow.

## Prerequisites

Before testing, ensure you have:

### Accounts & Credentials

- [ ] **Discord Bot Token** — Create at [Discord Developer Portal](https://discord.com/developers/applications)
  - Bot must have `MESSAGE CONTENT` intent enabled
  - Bot must have `VOICE` permission
- [ ] **Anthropic API Key** — From [console.anthropic.com](https://console.anthropic.com)
- [ ] **Discord Streaming Account** — A separate Discord account (not the bot) for web automation
  - Must be a member of the test server
  - Recommend using a dedicated test account

### Infrastructure

- [ ] **Docker** — Running and accessible (`docker ps` works)
- [ ] **Python 3.12+** — With jamie installed (`pip install -e .`)
- [ ] **CUA Sandbox Image** — Pre-pulled: `docker pull trycua/cua-xfce:latest`
- [ ] **Network Access** — Bot, agent, and sandbox can communicate on localhost

### Environment Setup

Create `.env` in the project root:

```bash
# Bot settings
JAMIE_BOT_DISCORD_TOKEN=your_bot_token
JAMIE_BOT_CUA_ENDPOINT=http://localhost:8000

# Agent settings  
JAMIE_AGENT_DISCORD_EMAIL=streaming_account@example.com
JAMIE_AGENT_DISCORD_PASSWORD=your_password
JAMIE_AGENT_ANTHROPIC_API_KEY=sk-ant-xxx
```

### Test Environment

- [ ] Discord test server with a voice channel
- [ ] Test user account (not the bot, not the streaming account)
- [ ] Bot invited to test server with appropriate permissions

---

## Test Procedure

### Phase 1: Bot Startup

**Terminal 1 — Start the Discord Bot**

```bash
cd ~/projects/jamie
source .venv/bin/activate
jamie-bot
```

**Expected Output:**
```
jamie_bot_starting
Bot logged in as Jamie#1234
Connected to N guilds
```

**Checklist:**
- [ ] Bot starts without errors
- [ ] Bot logs "Bot logged in as..."
- [ ] Bot shows as online in Discord

**If it fails:** See [Troubleshooting: Bot Won't Start](#bot-wont-start)

---

### Phase 2: Agent Startup

**Terminal 2 — Start the CUA Agent Controller**

```bash
cd ~/projects/jamie
source .venv/bin/activate
jamie-agent
```

**Expected Output:**
```
agent_starting host=0.0.0.0 port=8000 model=anthropic/claude-sonnet-4-5-20250929
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Checklist:**
- [ ] Agent starts without errors
- [ ] FastAPI server running on port 8000
- [ ] Health check passes: `curl http://localhost:8000/health`

**If it fails:** See [Troubleshooting: Agent Won't Start](#agent-wont-start)

---

### Phase 3: Send Stream Request

**From your test Discord account:**

1. Join a voice channel in the test server
2. Open a DM with Jamie bot
3. Send a URL:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

**Expected Bot Response:**
```
🎬 Starting stream...
Joining voice channel: General
```

**Checklist:**
- [ ] Bot acknowledges the URL
- [ ] Bot identifies your voice channel
- [ ] Bot forwards request to CUA agent (check Terminal 2 logs)

**If it fails:** See [Troubleshooting: URL Not Recognized](#url-not-recognized)

---

### Phase 4: CUA Automation

**Monitor Terminal 2 (Agent logs)**

The CUA agent will:
1. Spawn a Docker sandbox with browser
2. Log into Discord Web with streaming account
3. Navigate to the correct voice channel
4. Open the stream URL
5. Start screen sharing

**Expected Log Progression:**
```
sandbox_starting image=trycua/cua-xfce:latest
cua_task_started task=login_discord
cua_task_completed task=login_discord
cua_task_started task=join_voice_channel channel=General
cua_task_completed task=join_voice_channel
cua_task_started task=start_stream url=https://...
stream_active
```

**Checklist:**
- [ ] Sandbox container starts
- [ ] Discord login succeeds
- [ ] Voice channel join succeeds
- [ ] Screen share initiates

**If it fails:** See [Troubleshooting: CUA Automation Fails](#cua-automation-fails)

---

### Phase 5: Verify Streaming

**In Discord (test server voice channel):**

1. The streaming account should appear in voice
2. A "Screen" or "Live" indicator should show
3. Click to view the stream
4. Video/audio from the URL should be playing

**Checklist:**
- [ ] Streaming account visible in voice channel
- [ ] Stream is watchable by other users
- [ ] Audio is audible (if applicable)
- [ ] Video quality is acceptable

**Bot should send:**
```
✅ Now streaming: [URL Title]
```

---

### Phase 6: Stop Command

**From your test Discord account (DM to Jamie):**

```
stop
```

**Expected Response:**
```
🛑 Stopping stream...
Stream ended.
```

**Checklist:**
- [ ] Bot acknowledges stop command
- [ ] CUA agent receives stop signal (check Terminal 2)
- [ ] Screen share ends
- [ ] Streaming account leaves voice channel

---

### Phase 7: Clean Shutdown

**Terminal 2 — Stop the Agent**

Press `Ctrl+C`

**Expected:**
```
Shutting down...
Active sessions: 0
Cleanup complete.
```

**Checklist:**
- [ ] No orphaned Docker containers (`docker ps` shows none from jamie)
- [ ] Agent exits cleanly (exit code 0)

**Terminal 1 — Stop the Bot**

Press `Ctrl+C`

**Expected:**
```
keyboard_interrupt
initiating_graceful_shutdown
jamie_bot_stopped
```

**Checklist:**
- [ ] Bot disconnects from Discord gracefully
- [ ] Bot shows offline in Discord
- [ ] No error messages in logs

---

## Test Summary

| Phase | Description | Pass/Fail |
|-------|-------------|-----------|
| 1 | Bot Startup | ⬜ |
| 2 | Agent Startup | ⬜ |
| 3 | URL Request | ⬜ |
| 4 | CUA Automation | ⬜ |
| 5 | Stream Verification | ⬜ |
| 6 | Stop Command | ⬜ |
| 7 | Clean Shutdown | ⬜ |

---

## Troubleshooting

### Bot Won't Start

**Error: `JAMIE_BOT_DISCORD_TOKEN is not set`**
- Ensure `.env` file exists and contains `JAMIE_BOT_DISCORD_TOKEN=...`
- Check for typos in variable name

**Error: `Improper token has been passed`**
- Token is invalid or expired
- Regenerate token in Discord Developer Portal
- Make sure you copied the full token (they're long!)

**Error: `Privileged intent required`**
- Enable "Message Content Intent" in bot settings at Discord Developer Portal

### Agent Won't Start

**Error: `JAMIE_AGENT_ANTHROPIC_API_KEY is not set`**
- Add your Anthropic API key to `.env`

**Error: `Port 8000 already in use`**
- Another process is using the port
- Find it: `lsof -i :8000`
- Kill it or use a different port: `JAMIE_AGENT_PORT=8001 jamie-agent`

**Error: `Docker daemon not running`**
- Start Docker Desktop or the docker service
- Verify: `docker ps`

### URL Not Recognized

**Bot says "I don't understand that message"**
- Make sure you're sending a bare URL (not wrapped in text)
- Supported: YouTube, Twitch, Vimeo URLs
- Check bot is receiving DMs (not muted/blocked)

**Bot doesn't respond at all**
- Check Terminal 1 for errors
- Verify bot is online in Discord
- Try `help` command first

### CUA Automation Fails

**Error: `sandbox_start_failed`**
- Docker not running or image not pulled
- Run: `docker pull trycua/cua-xfce:latest`
- Check Docker has enough resources (4GB+ RAM recommended)

**Error: `login_failed`**
- Discord credentials incorrect
- Account may have 2FA (not supported yet)
- Account may be rate-limited — wait and retry

**Error: `voice_channel_not_found`**
- Streaming account not a member of the server
- Voice channel permissions blocking join
- Channel name mismatch

**Stream starts but no audio/video**
- Browser inside sandbox may need different codecs
- Try a different URL to isolate the issue
- Check sandbox logs: `docker logs <container_id>`

### Cleanup Issues

**Orphaned Docker containers**
```bash
# List jamie-related containers
docker ps -a | grep cua

# Force remove all
docker rm -f $(docker ps -a -q --filter "ancestor=trycua/cua-xfce:latest")
```

**Port still in use after shutdown**
```bash
# Find and kill the process
lsof -ti :8000 | xargs kill -9
lsof -ti :8080 | xargs kill -9
```

---

## Test URLs

Use these for testing different scenarios:

| URL | Type | Notes |
|-----|------|-------|
| `https://www.youtube.com/watch?v=dQw4w9WgXcQ` | YouTube | Classic, always works |
| `https://www.youtube.com/watch?v=jNQXAC9IVRw` | YouTube | First YouTube video ever |
| `https://www.twitch.tv/twitchpresents` | Twitch | Usually has content |
| `https://vimeo.com/347119375` | Vimeo | Test non-YouTube |

---

## Notes

- Full test cycle takes ~2-5 minutes depending on CUA speed
- First run may be slower (Docker image download, browser cache cold)
- Budget limit is $2.00/session by default — adjust `JAMIE_AGENT_MAX_BUDGET_PER_SESSION` if needed
- Logs are written to stdout — redirect to file for debugging: `jamie-bot 2>&1 | tee bot.log`
