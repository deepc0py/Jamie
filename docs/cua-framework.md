# CUA Framework - Comprehensive Reference

> **CUA** (Computer Use Agents) is an open-source platform for building, benchmarking, and deploying agents that can use any computer, with isolated, self-hostable sandboxes (Docker, QEMU, Apple Vz).

## Architecture Overview

CUA consists of three main components:

### 1. Desktop Sandboxes
Isolated virtual environments for safe agent execution:
- **Cloud Sandboxes** - Managed Linux, Windows, macOS hosted by CUA
- **Local Sandboxes** - Docker containers, QEMU VMs, macOS VMs (Lume), Windows Sandbox

### 2. Computer Framework (SDK)
Unified SDK for controlling desktop environments:
- Take screenshots and observe screens
- Simulate mouse clicks, movements, scrolling
- Type text and press keyboard shortcuts
- Run code and shell commands
- Works identically across all sandbox types

### 3. Agent Framework (SDK)
Build autonomous agents that see screens and complete tasks:
- 100+ VLM options (Cua VLM Router or direct provider access)
- Pre-built agent loops for computer-use tasks
- Composable architecture for grounding + planning models
- Built-in telemetry for monitoring

---

## Quick Start

### Installation

```bash
pip install cua-computer cua-agent
```

**Python Version:** Requires Python 3.12 or 3.13 (not 3.14 due to pydantic-core compatibility)

### Basic Agent Example

```python
from computer import Computer
from agent import ComputerAgent
import asyncio

async def main():
    async with Computer(
        os_type="linux",
        provider_type="docker",
        image="trycua/cua-xfce:latest"
    ) as computer:
        agent = ComputerAgent(
            model="anthropic/claude-sonnet-4-5-20250929",
            tools=[computer],
            max_trajectory_budget=5.0
        )
        
        async for result in agent.run("Open Firefox and search for Cua"):
            for item in result["output"]:
                if item["type"] == "message":
                    print(item["content"][0]["text"])

asyncio.run(main())
```

---

## Sandbox Setup

### Cloud Sandboxes

```bash
# Install CLI
curl -LsSf https://cua.ai/cli/install.sh | sh

# Login and create
cua auth login
cua sb create --os linux --size small --region north-america
```

### Docker (Linux Desktop)

```bash
# Pull lightweight XFCE image
docker pull --platform=linux/amd64 trycua/cua-xfce:latest

# OR full Ubuntu desktop
docker pull --platform=linux/amd64 trycua/cua-ubuntu:latest
```

### QEMU (Full VMs)

For Linux/Windows VMs with golden image preparation:

```bash
docker pull trycua/cua-qemu-linux:latest
# Requires Ubuntu 22.04 ISO and golden image creation step
```

### macOS (via Lume)

```bash
# Install Lume CLI
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/lume/scripts/install.sh)"

# Start macOS sandbox
lume run macos-sequoia-cua:latest
```

---

## Computer SDK Reference

### Computer Class

```python
from computer import Computer

computer = Computer(
    os_type="linux",           # "linux", "macos", "windows"
    provider_type="docker",    # "docker", "lume", "cloud", "qemu", "windows-sandbox", "host"
    image="trycua/cua-xfce:latest",
    display="1024x768",        # or {"width": 1920, "height": 1080}
    memory="8GB",
    cpu="4",
    timeout=100,
    api_key=None,              # For cloud provider
    shared_directories=[],     # Host dirs to share
    ephemeral=False,           # Data lost on stop if True
)
```

### Lifecycle Methods

```python
await computer.run()         # Start and connect
await computer.stop()        # Stop and release resources
await computer.restart()     # Restart
await computer.disconnect()  # Disconnect without stopping
ip = await computer.get_ip() # Get IP address
```

### Interface Methods

All accessed via `computer.interface`:

#### Mouse Actions

```python
await computer.interface.left_click(x, y)
await computer.interface.right_click(x, y)
await computer.interface.double_click(x, y)
await computer.interface.mouse_down(x, y, button="left")
await computer.interface.mouse_up(x, y, button="left")
await computer.interface.move_cursor(x, y)
await computer.interface.drag_to(x, y, button="left", duration=0.5)
await computer.interface.drag(path, button="left", duration=0.5)  # path = [(x,y), ...]
await computer.interface.scroll(x, y)  # positive y = up, negative = down
await computer.interface.scroll_down(clicks=1)
await computer.interface.scroll_up(clicks=1)
```

#### Keyboard Actions

```python
from computer.interface.models import Key

await computer.interface.type_text("Hello, World!")
await computer.interface.press(Key.ENTER)
await computer.interface.hotkey(Key.CTRL, Key.C)  # Keyboard shortcuts
await computer.interface.key_down(Key.SHIFT)
await computer.interface.key_up(Key.SHIFT)
```

**Available Keys:**
- Navigation: `PAGE_DOWN`, `PAGE_UP`, `HOME`, `END`, `LEFT`, `RIGHT`, `UP`, `DOWN`
- Special: `RETURN`/`ENTER`, `ESCAPE`/`ESC`, `TAB`, `SPACE`, `BACKSPACE`, `DELETE`
- Modifiers: `ALT`, `CTRL`, `SHIFT`, `WIN`, `COMMAND`, `OPTION`
- Function: `F1` through `F12`

#### Screen Methods

```python
screenshot_bytes = await computer.interface.screenshot()
screenshot_bytes = await computer.interface.screenshot(
    boxes=[{"x": 100, "y": 100, "width": 200, "height": 150}],
    box_color="#FF0000",
    scale_factor=0.5
)
size = await computer.interface.get_screen_size()  # {"width": 1920, "height": 1080}
pos = await computer.interface.get_cursor_position()  # {"x": 500, "y": 300}
```

#### File Operations

```python
content = await computer.interface.read_text("/home/user/file.txt")
await computer.interface.write_text("/home/user/file.txt", "content")
data = await computer.interface.read_bytes("/home/user/image.png", offset=0, length=None)
await computer.interface.write_bytes("/home/user/image.png", bytes_data, append=False)
exists = await computer.interface.file_exists("/path/to/file")
exists = await computer.interface.directory_exists("/path/to/dir")
size = await computer.interface.get_file_size("/path/to/file")
files = await computer.interface.list_dir("/home/user")
await computer.interface.create_dir("/home/user/new_folder")
await computer.interface.delete_file("/home/user/old_file.txt")
await computer.interface.delete_dir("/home/user/old_folder")
```

#### Shell Commands

```python
result = await computer.interface.run_command("ls -la")
print(result.stdout)
print(result.stderr)
print(result.returncode)  # 0 = success
```

#### Clipboard

```python
text = await computer.interface.copy_to_clipboard()
await computer.interface.set_clipboard("Text to copy")
```

#### Window Management

```python
window_id = await computer.interface.launch("firefox", ["--private-window"])
await computer.interface.open("https://www.google.com")
window_id = await computer.interface.get_current_window_id()
windows = await computer.interface.get_application_windows("firefox")
title = await computer.interface.get_window_name(window_id)
width, height = await computer.interface.get_window_size(window_id)
x, y = await computer.interface.get_window_position(window_id)
await computer.interface.set_window_size(window_id, 1200, 800)
await computer.interface.set_window_position(window_id, 100, 100)
await computer.interface.maximize_window(window_id)
await computer.interface.minimize_window(window_id)
await computer.interface.activate_window(window_id)
await computer.interface.close_window(window_id)
```

#### Accessibility

```python
tree = await computer.interface.get_accessibility_tree()
bounds = await computer.interface.get_active_window_bounds()  # {x, y, width, height}
```

### Python Execution in Sandbox

```python
# Execute function in sandbox
def calculate(x, y):
    return x + y
result = await computer.python_exec(calculate, 5, 10)

# Background execution
task_id = await computer.python_exec_background(long_running_func)

# Install packages
await computer.pip_install(["requests", "pandas==2.0.0"])

# Virtual environments
await computer.venv_install("my_env", ["requests", "pandas"])
result = await computer.venv_cmd("my_env", "pip list")
result = await computer.venv_exec("my_env", process_data, data)
task_id = await computer.venv_exec_background("my_env", long_task)
```

### Tracing

```python
await computer.tracing.start({
    "name": "my-workflow",
    "screenshots": True,
    "api_calls": True,
    "accessibility_tree": False,
    "metadata": True
})

await computer.tracing.add_metadata("workflow", "login-flow")

trace_path = await computer.tracing.stop({"format": "zip"})
```

---

## Agent SDK Reference

### ComputerAgent Class

```python
from agent import ComputerAgent

agent = ComputerAgent(
    model="anthropic/claude-sonnet-4-5-20250929",  # Required
    tools=[computer],                               # Required
    api_key=None,                                   # Provider env var default
    callbacks=[],                                   # Callback handlers
    instructions=None,                              # Custom instructions
    verbosity=None,                                 # Logging level
    max_trajectory_budget=None,                     # Max cost in dollars
    only_n_most_recent_images=None,                 # Limit screenshots
    trajectory_dir=None,                            # Save trajectories
)
```

### Running Tasks

```python
# Streaming results
async for result in agent.run("Open Firefox and search for Cua"):
    for item in result["output"]:
        match item["type"]:
            case "message":
                print(item["content"][0]["text"])
            case "computer_call":
                print(f"Action: {item['action']['type']}")
            case "computer_call_output":
                print(f"Output received")
    print(f"Cost so far: ${result['usage']['response_cost']:.4f}")

# Run to completion
result = await agent.run_to_completion("Open the calculator app")

# Multi-turn conversation
messages = [
    {"role": "user", "content": "Take a screenshot"},
    {"role": "assistant", "content": "Done. I can see a desktop."},
    {"role": "user", "content": "Now click the search bar"}
]
async for result in agent.run(messages):
    process(result)

# Streaming responses
async for result in agent.run(messages, stream=True):
    for item in result["output"]:
        if item["type"] == "message":
            print(item["content"][0]["text"], end="", flush=True)
```

### Agent Loop Lifecycle

1. **Observe** → Take a screenshot
2. **Reason** → VLM decides next action
3. **Act** → Execute (click, type, scroll)
4. **Repeat** → Until done

### Budget Control

```python
from agent.exceptions import BudgetExceededException

agent = ComputerAgent(
    model="anthropic/claude-sonnet-4-5-20250929",
    tools=[computer],
    max_trajectory_budget=5.0  # Max $5 per run
)

try:
    async for result in agent.run(messages):
        process(result)
except BudgetExceededException:
    print("Task exceeded budget limit")
```

---

## Callbacks

### Built-in Callbacks

```python
from agent.callbacks import (
    LoggingCallback,
    BudgetManagerCallback,
    ImageRetentionCallback,
    TrajectorySaverCallback,
    PromptInstructionsCallback
)

agent = ComputerAgent(
    model="...",
    tools=[computer],
    callbacks=[
        LoggingCallback(level=logging.DEBUG),
        BudgetManagerCallback(max_budget=10.0, reset_after_each_run=True),
        ImageRetentionCallback(only_n_most_recent_images=3),
        TrajectorySaverCallback(trajectory_dir="trajectories"),
        PromptInstructionsCallback("Always confirm before clicking"),
    ]
)
```

### Custom Callbacks

```python
from agent.callbacks.base import AsyncCallbackHandler

class MyCallback(AsyncCallbackHandler):
    async def on_run_start(self, kwargs, old_items):
        print("Starting run...")

    async def on_run_continue(self, kwargs, old_items, new_items) -> bool:
        return True  # Return False to stop

    async def on_llm_start(self, messages):
        return messages  # Preprocess

    async def on_llm_end(self, messages):
        return messages  # Postprocess

    async def on_usage(self, usage):
        print(f"Cost: ${usage.response_cost:.4f}")

    async def on_computer_call_start(self, item):
        pass

    async def on_computer_call_end(self, item, result):
        pass

    async def on_screenshot(self, screenshot, name):
        pass

    async def on_run_end(self, kwargs, old_items, new_items):
        print("Run complete!")
```

---

## Custom Tools

### Function Tools

```python
def calculate(a: int, b: int) -> int:
    """Calculate the sum of two integers"""
    return a + b

async def fetch_data(url: str) -> str:
    """Fetch data from a URL"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

agent = ComputerAgent(
    model="anthropic/claude-sonnet-4-5-20250929",
    tools=[computer, calculate, fetch_data]
)
```

### Sandboxed Tools

```python
from computer.helpers import sandboxed

@sandboxed()
def read_sandbox_file(path: str) -> str:
    """Read a file from inside the sandbox"""
    with open(path, 'r') as f:
        return f.read()

@sandboxed(venv_name="my_env", computer=computer, max_retries=5)
def process_data(data: list) -> dict:
    """Process data inside the sandbox"""
    import pandas as pd
    df = pd.DataFrame(data)
    return df.describe().to_dict()
```

### BaseTool Class

```python
from agent.tools import BaseTool, register_tool, ToolError

@register_tool("database_query")
class DatabaseQueryTool(BaseTool):
    def __init__(self, connection_string: str):
        self.connection = connection_string

    @property
    def description(self) -> str:
        return "Execute a read-only SQL query"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL SELECT query"}
            },
            "required": ["query"]
        }

    def call(self, params, **kwargs):
        query = params["query"] if isinstance(params, dict) else params
        # Execute and return results
        return {"rows": [...]}
```

### Tool Errors

```python
from agent.tools import ToolError

def divide(a: float, b: float) -> float:
    """Divide a by b"""
    if b == 0:
        raise ToolError("Cannot divide by zero")
    return a / b
```

---

## Browser Tool

For browser-optimized models (Gemini 2.5, Microsoft Fara):

```python
from agent.tools import BrowserTool

browser = BrowserTool(interface=computer)

agent = ComputerAgent(
    model="gemini-2.5-computer-use-preview-10-2025",
    tools=[browser]
)

# Programmatic usage
await browser.visit_url("https://example.com")
screenshot = await browser.screenshot()
await browser.click(x=500, y=300)
await browser.type("Hello")
await browser.scroll(delta_x=0, delta_y=500)
await browser.web_search("Python documentation")
await browser.history_back()
```

**Browser Tool vs Computer Tool:**
| Feature | Browser Tool | Computer Tool |
|---------|-------------|---------------|
| Direct URL navigation | ✅ | ❌ |
| Web search action | ✅ | ❌ |
| History navigation | ✅ | ❌ |
| Desktop applications | ❌ | ✅ |
| System dialogs | ❌ | ✅ |
| Multi-application workflows | ❌ | ✅ |

---

## Vision Language Models (VLMs)

### Model Format

```python
# provider/model-name
agent = ComputerAgent(model="anthropic/claude-sonnet-4-5-20250929", ...)
agent = ComputerAgent(model="openai/computer-use-preview", ...)
agent = ComputerAgent(model="google/gemini-2.5-flash", ...)
agent = ComputerAgent(model="ollama/ui-tars:latest", ...)
```

### Composed Models

```python
# UI-TARS for grounding, Claude for planning
agent = ComputerAgent(
    model="ollama/ui-tars:latest+anthropic/claude-sonnet-4-5-20250929",
    tools=[computer]
)
```

### Model Categories

**Full Computer-Use:**
- Anthropic Claude (all versions)
- OpenAI computer-use-preview
- UI-TARS (ByteDance)
- Qwen 2.5 VL (Alibaba)

**Browser-Only:**
- Gemini 2.5 Computer-Use (Google)
- Fara (Microsoft)

**Grounding-Only (must compose):**
- GTA1, OmniParser, Moondream3

### Local Models

```python
# HuggingFace
agent = ComputerAgent(model="huggingface-local/ByteDance-Seed/UI-TARS-1.5-7B", tools=[computer])

# MLX (Apple Silicon)
agent = ComputerAgent(model="mlx/mlx-community/UI-TARS-1.5-7B-6bit", tools=[computer])

# Ollama
agent = ComputerAgent(model="ollama_chat/llama3.2:latest", tools=[computer])
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CUA_API_KEY` | API key for cloud provider/VLM Router |
| `ANTHROPIC_API_KEY` | Anthropic models |
| `OPENAI_API_KEY` | OpenAI models |
| `GOOGLE_API_KEY` | Google models |
| `OLLAMA_HOST` | Ollama host (default: localhost:11434) |
| `CUA_REGION` | Default region for cloud provider |
| `DOCKER_HOST` | Custom Docker host |
| `LUME_HOST` | Custom Lume API host (default: localhost:7777) |

---

## Cloud Provider API

### Python SDK

```python
from computer.providers.cloud.provider import CloudProvider

provider = CloudProvider(verbose=False)

async with provider:
    vms = await provider.list_vms()
    info = await provider.get_vm("my-vm-name")
    await provider.run_vm("my-vm-name")
    await provider.stop_vm("my-vm-name")
    await provider.restart_vm("my-vm-name")
```

### HTTP API

```bash
# List sandboxes
curl -H "Authorization: Bearer $CUA_API_KEY" "https://api.cua.ai/v1/vms"

# Start/Stop/Restart
curl -X POST -H "Authorization: Bearer $CUA_API_KEY" "https://api.cua.ai/v1/vms/my-vm-name/start"
curl -X POST -H "Authorization: Bearer $CUA_API_KEY" "https://api.cua.ai/v1/vms/my-vm-name/stop"
curl -X POST -H "Authorization: Bearer $CUA_API_KEY" "https://api.cua.ai/v1/vms/my-vm-name/restart"
```

### Sandbox Status Values

| Status | Description |
|--------|-------------|
| `pending` | Deployment in progress |
| `running` | Active and accessible |
| `stopped` | Stopped but not terminated |
| `terminated` | Permanently destroyed |
| `failed` | Deployment or operation failed |

---

## Use Cases

- **AI coding assistants** - Isolated code execution for Claude Code, Codex CLI, OpenCode
- **Computer-use agents** - Autonomous desktop application control
- **Workflow automation** - Automate repetitive tasks across applications
- **Testing** - End-to-end tests with real UIs
- **Benchmarks** - OSWorld, ScreenSpot evaluation
- **Research** - Build, evaluate, train computer-use AI agents

---

## Links

- **Documentation:** https://cua.ai/docs
- **Discord:** https://discord.com/invite/cua-ai
- **GitHub:** https://github.com/trycua/cua
