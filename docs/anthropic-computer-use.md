# Anthropic Computer Use Tool - Comprehensive Documentation

> **Last Updated:** February 2026  
> **Status:** Beta Feature  
> **Source:** https://docs.anthropic.com/en/docs/agents-and-tools/computer-use

## Overview

Claude's Computer Use Tool enables Claude to interact with desktop environments through screenshot capture and mouse/keyboard control for autonomous desktop interaction. This is a **beta feature** that allows Claude to "see" a screen and control a computer like a human operator.

### Core Capabilities

- **Screenshot Capture** - See what's currently displayed on screen
- **Mouse Control** - Click, drag, and move the cursor
- **Keyboard Input** - Type text and use keyboard shortcuts
- **Desktop Automation** - Interact with any application or interface

Computer use works through an "agent loop" where Claude requests actions, your application executes them in a sandboxed environment, and returns results (screenshots, outputs) back to Claude.

---

## Model Compatibility

| Model | Tool Version | Beta Flag |
|-------|-------------|-----------|
| Claude Opus 4.6, Claude Opus 4.5 | `computer_20251124` | `computer-use-2025-11-24` |
| Claude Sonnet 4.5, Haiku 4.5, Opus 4.1, Sonnet 4, Opus 4 | `computer_20250124` | `computer-use-2025-01-24` |
| Claude Sonnet 3.7 (deprecated) | `computer_20250124` | `computer-use-2025-01-24` |

**Important:** Older tool versions are NOT backwards-compatible with newer models. Always use the tool version matching your model version.

---

## API Usage

### Required Headers

Computer use requires a beta header in all API requests:

```
anthropic-beta: computer-use-2025-11-24  # For Opus 4.5/4.6
anthropic-beta: computer-use-2025-01-24  # For other models
```

### Basic API Request (Python)

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-opus-4-6",  # or another compatible model
    max_tokens=1024,
    tools=[
        {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": 1024,
            "display_height_px": 768,
            "display_number": 1,
        },
        {
            "type": "text_editor_20250728",
            "name": "str_replace_based_edit_tool"
        },
        {
            "type": "bash_20250124",
            "name": "bash"
        }
    ],
    messages=[{"role": "user", "content": "Save a picture of a cat to my desktop."}],
    betas=["computer-use-2025-11-24"]
)
print(response)
```

### Shell/cURL Example

```bash
curl https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: computer-use-2025-01-24" \
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 2000,
    "tools": [
      {
        "type": "computer_20250124",
        "name": "computer",
        "display_width_px": 1024,
        "display_height_px": 768,
        "display_number": 1
      }
    ],
    "messages": [
      {"role": "user", "content": "Take a screenshot of the desktop."}
    ]
  }'
```

---

## Tool Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `type` | Yes | Tool version: `computer_20251124`, `computer_20250124`, or `computer_20241022` |
| `name` | Yes | Must be `"computer"` |
| `display_width_px` | Yes | Display width in pixels |
| `display_height_px` | Yes | Display height in pixels |
| `display_number` | No | Display number for X11 environments |
| `enable_zoom` | No | Enable zoom action (`computer_20251124` only). Default: `false` |

---

## Supported Actions

### Basic Actions (All Versions)

| Action | Description |
|--------|-------------|
| `screenshot` | Capture the current display |
| `left_click` | Click at coordinates `[x, y]` |
| `type` | Type a text string |
| `key` | Press key or combination (e.g., "ctrl+s") |
| `mouse_move` | Move cursor to coordinates |

### Enhanced Actions (`computer_20250124`)

Available in Claude 4 models and Claude Sonnet 3.7:

| Action | Description |
|--------|-------------|
| `scroll` | Scroll in any direction with amount control |
| `left_click_drag` | Click and drag between coordinates |
| `right_click` | Right mouse button click |
| `middle_click` | Middle mouse button click |
| `double_click` | Double-click at position |
| `triple_click` | Triple-click at position |
| `left_mouse_down` | Press and hold left mouse button |
| `left_mouse_up` | Release left mouse button |
| `hold_key` | Hold down a key for specified duration (seconds) |
| `wait` | Pause between actions |

### Enhanced Actions (`computer_20251124`)

Available in Claude Opus 4.6 and Claude Opus 4.5:

- All actions from `computer_20250124`
- `zoom` - View a specific region at full resolution. Requires `enable_zoom: true`. Takes `region` parameter with coordinates `[x1, y1, x2, y2]` defining top-left and bottom-right corners.

### Modifier Keys

Click and scroll actions support modifier keys:

```json
{
  "action": "left_click",
  "coordinate": [500, 300],
  "modifiers": ["ctrl", "shift"]
}
```

---

## The Agent Loop

Computer use operates through an "agent loop" - a cycle of request/response between Claude and your application:

1. **Provide tools and prompt** - Send computer use tool + user request to Claude
2. **Claude requests tool use** - Response contains `stop_reason: "tool_use"`
3. **Execute and return results** - Your app executes the action, captures screenshot, returns as `tool_result`
4. **Repeat until complete** - Claude continues requesting tools until task is done

### Example Agent Loop Implementation

```python
async def sampling_loop(
    *,
    model: str,
    messages: list[dict],
    api_key: str,
    max_tokens: int = 4096,
    tool_version: str,
    thinking_budget: int | None = None,
    max_iterations: int = 10,  # Prevent infinite loops
):
    client = Anthropic(api_key=api_key)
    beta_flag = "computer-use-2025-01-24" if "20250124" in tool_version else "computer-use-2024-10-22"
    
    tools = [
        {"type": f"computer_{tool_version}", "name": "computer", 
         "display_width_px": 1024, "display_height_px": 768},
        {"type": f"text_editor_{tool_version}", "name": "str_replace_editor"},
        {"type": f"bash_{tool_version}", "name": "bash"}
    ]
    
    iterations = 0
    while True and iterations < max_iterations:
        iterations += 1
        
        thinking = None
        if thinking_budget:
            thinking = {"type": "enabled", "budget_tokens": thinking_budget}
        
        response = client.beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            tools=tools,
            betas=[beta_flag],
            thinking=thinking
        )
        
        response_content = response.content
        messages.append({"role": "assistant", "content": response_content})
        
        tool_results = []
        for block in response_content:
            if block.type == "tool_use":
                # Execute the tool here
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        
        if not tool_results:
            return messages  # Task complete
        
        messages.append({"role": "user", "content": tool_results})
```

---

## Computing Environment Requirements

Computer use requires a sandboxed environment:

- **Virtual Display** - X11 display server (Xvfb) for rendering
- **Desktop Environment** - Window manager (Mutter) and panel (Tint2) on Linux
- **Applications** - Firefox, LibreOffice, text editors, file managers
- **Tool Implementations** - Code translating Claude's requests into actual actions
- **Agent Loop** - Program handling Claude↔environment communication

### Reference Implementation

Anthropic provides a Docker-based reference implementation:

```bash
export ANTHROPIC_API_KEY=%your_api_key%
docker run \
    -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -v $HOME/.anthropic:/home/computeruse/.anthropic \
    -p 5900:5900 \
    -p 8501:8501 \
    -p 6080:6080 \
    -p 8080:8080 \
    -it ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest
```

**Access Points:**
- Combined interface: http://localhost:8080
- Streamlit only: http://localhost:8501
- Desktop view: http://localhost:6080/vnc.html
- VNC: vnc://localhost:5900

**GitHub:** https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo

---

## Coordinate Scaling for High Resolutions

The API constrains images to max 1568px on longest edge (~1.15 megapixels). For higher resolutions, you must handle coordinate scaling:

```python
import math

def get_scale_factor(width, height):
    """Calculate scale factor to meet API constraints."""
    long_edge = max(width, height)
    total_pixels = width * height
    long_edge_scale = 1568 / long_edge
    total_pixels_scale = math.sqrt(1_150_000 / total_pixels)
    return min(1.0, long_edge_scale, total_pixels_scale)

# When capturing screenshot
scale = get_scale_factor(screen_width, screen_height)
scaled_width = int(screen_width * scale)
scaled_height = int(screen_height * scale)

# Resize image before sending to Claude
screenshot = capture_and_resize(scaled_width, scaled_height)

# When handling Claude's coordinates, scale them back up
def execute_click(x, y):
    screen_x = x / scale
    screen_y = y / scale
    perform_click(screen_x, screen_y)
```

**Recommended:** Use XGA resolution (1024x768) for best accuracy.

---

## Extended Thinking Support

Claude 4 models support "thinking" mode for visibility into reasoning:

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=[...],
    messages=[...],
    betas=["computer-use-2025-11-24"],
    thinking={
        "type": "enabled",
        "budget_tokens": 1024
    }
)
```

Benefits:
- Understand decision-making process
- Debug issues and misconceptions
- Learn from Claude's approach
- Visibility into multi-step operations

---

## Security Considerations

⚠️ **Computer use has unique risks distinct from standard API features.**

### Critical Precautions

1. **Use dedicated VM/container** with minimal privileges
2. **Avoid sensitive data access** - no account logins in environment
3. **Limit internet access** to allowlisted domains
4. **Human confirmation** for consequential actions (financial, ToS acceptance)

### Prompt Injection Risks

- Claude may follow commands found in screenshots or webpages
- Can override user instructions
- Anthropic runs automatic classifiers to flag potential injections
- Classifiers trigger user confirmation requests when risks detected
- Contact support to opt out of automatic protection

### Required User Disclosure

Inform end users of risks and obtain consent before enabling computer use in products.

---

## Prompting Best Practices

1. **Simple, well-defined tasks** with explicit step-by-step instructions
2. **Verification prompts:** `"After each step, take a screenshot and evaluate if you achieved the right outcome. Explicitly show thinking: 'I have evaluated step X...'"`
3. **Keyboard shortcuts** for tricky UI elements (dropdowns, scrollbars)
4. **Example screenshots** for repeatable tasks
5. **Credentials in XML tags:** `<robot_credentials>` (with caution - review prompt injection guide)
6. **System prompts** for known issues or recurring tasks

---

## Limitations & Gotchas

1. **Beta status** - API subject to change
2. **Single session** - Reference implementation supports one session at a time
3. **Image size constraints** - Max 1568px longest edge, ~1.15 megapixels
4. **Resolution matters** - Scaling affects accuracy; XGA (1024x768) recommended
5. **Latency** - Agent loop involves multiple API round-trips
6. **Cost** - Each screenshot + action cycle consumes tokens; implement iteration limits
7. **Tool version mismatch** - Must match model version exactly
8. **Environment setup** - Requires containerized Linux desktop (no direct macOS/Windows support)
9. **Prompt injection vulnerability** - Can be manipulated by on-screen content

---

## Comparison with Other Computer Use Frameworks

| Feature | Anthropic Computer Use | OpenAI Operator | Open Interpreter |
|---------|----------------------|-----------------|------------------|
| **Architecture** | API + Your Environment | Hosted Browser | Local Execution |
| **Environment Control** | Full (you implement) | Limited (browser only) | Full (your machine) |
| **Safety Model** | Sandboxed VM required | Hosted sandboxing | User responsibility |
| **Vision Support** | Screenshots (scaled) | Native browser | Screenshots |
| **Action Types** | Mouse, keyboard, bash, text edit | Browser actions | Shell commands |
| **Multi-platform** | Linux container | Browser | Cross-platform |
| **Thinking/Reasoning** | Yes (extended thinking) | Limited | Varies |

**Key Differentiator:** Anthropic's approach requires YOU to implement the execution environment, giving maximum flexibility but requiring more setup. The model only provides the intelligence layer - all actual computer control is your responsibility.

---

## Platform Availability

- **Direct API** - Full support
- **Amazon Bedrock** - Supported (request model access first)
- **Google Vertex AI** - Supported
- **Microsoft Foundry** - Check current availability

---

## Resources

- **Documentation:** https://docs.anthropic.com/en/docs/agents-and-tools/computer-use
- **Reference Implementation:** https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo
- **Feedback Form:** https://forms.gle/BT1hpBrqDPDUrCqo7
- **Beta Headers Info:** https://docs.anthropic.com/en/docs/api/beta-headers
- **Prompt Injection Guide:** https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks

---

## Quick Reference

```python
# Minimal computer use setup
import anthropic

client = anthropic.Anthropic()
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=[{
        "type": "computer_20251124",
        "name": "computer",
        "display_width_px": 1024,
        "display_height_px": 768,
    }],
    messages=[{"role": "user", "content": "Your task here"}],
    betas=["computer-use-2025-11-24"]
)

# Handle response
for block in response.content:
    if block.type == "tool_use":
        action = block.input["action"]
        # Execute action in your environment
        # Return screenshot as tool_result
```

---

*This documentation compiled from official Anthropic sources. For the most current information, always refer to the official documentation.*
