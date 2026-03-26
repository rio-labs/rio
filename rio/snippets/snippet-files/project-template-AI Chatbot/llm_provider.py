"""
LLM provider configuration for the AI Chatbot template.

Supports multiple LLM providers via the OpenAI-compatible API interface.
Currently supported: OpenAI, MiniMax.

Configure via environment variables:
  LLM_PROVIDER  — Force a specific provider ("openai" or "minimax")
  OPENAI_API_KEY  — API key for OpenAI
  MINIMAX_API_KEY — API key for MiniMax
"""

import dataclasses
import os
import typing as t

import openai  # type: ignore (hidden from user)


@dataclasses.dataclass
class LLMConfig:
    """
    Stores which LLM provider to use and how to connect to it.
    Attached to the Rio app so every component can retrieve it.
    """

    provider: str
    model: str
    provider_name: str


# Provider presets — all use the OpenAI-compatible chat completions API
PROVIDERS: dict[str, dict[str, t.Any]] = {
    "openai": {
        "name": "OpenAI",
        "base_url": None,  # SDK default
        "default_model": "gpt-3.5-turbo",
        "api_key_env": "OPENAI_API_KEY",
    },
    "minimax": {
        "name": "MiniMax",
        "base_url": "https://api.minimax.io/v1",
        "default_model": "MiniMax-M2.7",
        "api_key_env": "MINIMAX_API_KEY",
    },
}


def detect_provider() -> (
    tuple[openai.AsyncOpenAI, LLMConfig] | tuple[None, None]
):
    """
    Detect which LLM provider to use based on environment variables.

    Priority:
      1. ``LLM_PROVIDER`` env var selects a specific provider.
      2. Auto-detect by checking which API key is set.

    Returns ``(client, config)`` on success, or ``(None, None)`` when
    no API key is available.
    """
    provider_name = os.environ.get("LLM_PROVIDER", "").lower().strip()

    # Explicit provider selection
    if provider_name and provider_name in PROVIDERS:
        preset = PROVIDERS[provider_name]
        api_key = os.environ.get(preset["api_key_env"])
        if api_key:
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=preset["base_url"],
            )
            config = LLMConfig(
                provider=provider_name,
                model=os.environ.get("LLM_MODEL", preset["default_model"]),
                provider_name=preset["name"],
            )
            return client, config

    # Auto-detect from available API keys
    for key, preset in PROVIDERS.items():
        api_key = os.environ.get(preset["api_key_env"])
        if api_key:
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=preset["base_url"],
            )
            config = LLMConfig(
                provider=key,
                model=os.environ.get("LLM_MODEL", preset["default_model"]),
                provider_name=preset["name"],
            )
            return client, config

    return None, None
