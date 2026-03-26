# <additional-imports>
import openai  # type: ignore (hidden from user)

import rio

from . import llm_provider  # type: ignore (hidden from user)

# </additional-imports>


# <additional-code>
# Detect the LLM provider from environment variables.
#
# Supported providers:
#   - OpenAI:  set OPENAI_API_KEY
#   - MiniMax: set MINIMAX_API_KEY  (OpenAI-compatible API)
#
# You can also force a specific provider with LLM_PROVIDER="openai" or
# LLM_PROVIDER="minimax", and override the model with LLM_MODEL.

LLM_CLIENT, LLM_CONFIG = llm_provider.detect_provider()

if LLM_CLIENT is None:
    print(
        """
This template requires an LLM API key to work.

Supported providers:
  - OpenAI:  set OPENAI_API_KEY  (https://platform.openai.com/api-keys)
  - MiniMax: set MINIMAX_API_KEY (https://platform.minimax.io)

You can also set LLM_PROVIDER to choose a specific provider,
and LLM_MODEL to override the default model.
""".strip()
    )
    LLM_CONFIG = llm_provider.LLMConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        provider_name="OpenAI",
    )


def on_app_start(app: rio.App) -> None:
    # Attach the LLM client and config so components can retrieve them
    if LLM_CLIENT is not None:
        app.default_attachments.append(LLM_CLIENT)

    app.default_attachments.append(LLM_CONFIG)


# </additional-code>
