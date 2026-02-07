# Jamie

**Discord URL Streamer powered by Computer Use Agent (CUA)**

Jamie is a Discord bot that streams web content (YouTube, Twitch, Vimeo, etc.) to voice channels. Send Jamie a URL via DM while you're in a voice channel, and it will join and stream the content for everyone to watch together.

## How It Works

```
┌─────────────┐     DM with URL     ┌─────────────┐
│   Discord   │ ─────────────────▶  │  Jamie Bot  │
│    User     │                     │ (discord.py)│
└─────────────┘                     └──────┬──────┘
                                           │
                                           │ HTTP API
                                           ▼
                                    ┌─────────────┐
                                    │     CUA     │
                                    │ Controller  │
                                    └──────┬──────┘
                                           │
                                           │ Docker
                                           ▼
                                    ┌─────────────┐
                                    │   Browser   │
                                    │  (Firefox)  │
                                    └─────────────┘
```

1. **User** joins a voice channel and DMs Jamie with a URL
2. **Jamie Bot** detects the user's voice channel and sends request to CUA Controller
3. **CUA Controller** spawns a Docker sandbox with a browser
4. **CUA Agent** (Claude vision model) automates Discord:
   - Logs into Discord Web
   - Joins the voice channel
   - Opens the URL
   - Shares screen to stream content
5. **User** watches with friends!

## Project Structure

```
jamie/
├── bot/                 # Discord bot (receives DMs, manages sessions)
│   ├── main.py          # Bot entry point
│   ├── handlers.py      # Message handlers
│   ├── session.py       # Session state management
│   └── cua_client.py    # HTTP client for CUA Controller
├── agent/               # CUA Controller (automates Discord)
│   ├── main.py          # FastAPI server entry point
│   ├── controller.py    # HTTP API endpoints
│   ├── streamer.py      # CUA streaming agent
│   └── prompts.py       # Discord automation prompts
├── shared/              # Shared code
│   ├── models.py        # Pydantic models for API
│   ├── errors.py        # Error codes
│   └── config.py        # Configuration management
├── tests/               # Test suite
├── docker/              # Docker configurations
├── pyproject.toml       # Project metadata
└── docs/                # Documentation
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker 24.0+
- Discord Bot Token
- Anthropic API Key
- A Discord account for streaming (separate from bot)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/jamie.git
cd jamie

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### Running

```bash
# Terminal 1: Start CUA Controller
uvicorn jamie.agent.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Discord Bot
python -m jamie.bot.main
```

## Usage

1. Invite Jamie to your Discord server
2. Join a voice channel
3. DM Jamie with a URL:
   ```
   https://youtube.com/watch?v=dQw4w9WgXcQ
   ```
4. Wait ~30-60 seconds for setup
5. Watch together!

### Commands (via DM)

- **URL**: Start streaming the URL to your voice channel
- `stop`: End the current stream
- `status`: Check streaming status
- `help`: Show usage information

## Development

See [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) for full technical specification.

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy .
```

## License

MIT
