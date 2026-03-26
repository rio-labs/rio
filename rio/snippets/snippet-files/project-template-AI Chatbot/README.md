This example shows off a simple AI-Chat that supports multiple LLM providers out
of the box. You can talk to **OpenAI** or **MiniMax** large language models — just
set the right environment variable and the template auto-detects the provider.

**This example requires an LLM API key to function.**

### Supported Providers

| Provider | API Key Variable | Models | Docs |
|----------|-----------------|--------|------|
| OpenAI | `OPENAI_API_KEY` | `gpt-3.5-turbo` (default) | [platform.openai.com](https://platform.openai.com/api-keys) |
| MiniMax | `MINIMAX_API_KEY` | `MiniMax-M2.7`, `MiniMax-M2.7-highspeed` | [platform.minimax.io](https://platform.minimax.io) |

### Quick Start

```bash
# Option A: Use OpenAI
export OPENAI_API_KEY="sk-..."

# Option B: Use MiniMax
export MINIMAX_API_KEY="your-minimax-key"

# Optional: force a specific provider and model
export LLM_PROVIDER="minimax"
export LLM_MODEL="MiniMax-M2.7-highspeed"
```

The app has a single chat page, where you can type in a message and get a
response. If there aren't any messages yet, the bot displays a placeholder with
helpful suggestions to the user. Once the first message is entered, it switches
to a conversation view.

A progress circle indicates to the user when the bot is busy generating a
response.

## Lessons

In this example you can see how to:

- Interact with an external API
- Support multiple LLM providers via the OpenAI-compatible API
- Make components communicate via custom events

## Components

This project contains 5 components:

1. `ChatMessage`: Displays a single chat message with a colored background.
2. `ChatSuggestionCard`: A clickable component containing a suggested
   conversation starter.
3. `EmptyChatPlaceholder`: A placeholder displayed when there is no chat
   history.
4. `GeneratingResponsePlaceholder`: A placeholder displayed while the AI is
   generating its response.
5. `ChatPage`: The core of the app that combines the other components as
   necessary.
