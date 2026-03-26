"""
Tests for the AI Chatbot template's LLM provider system.

Covers provider detection, configuration, and the conversation module's
multi-provider support.
"""

from __future__ import annotations

import ast
import importlib
import os
import sys
import types
import typing as t
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Locate the template directory and import llm_provider / conversation as
# plain modules (they don't need the full rio import chain).
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / (
    "rio/snippets/snippet-files/project-template-AI Chatbot"
)


def _load_module(name: str, path: Path) -> types.ModuleType:
    """Import a single .py file as a module, skipping any ``openai`` import
    by injecting a lightweight stub."""
    source = path.read_text()
    tree = ast.parse(source)
    code = compile(tree, str(path), "exec")
    mod = types.ModuleType(name)
    mod.__file__ = str(path)

    # Provide a minimal openai stub so the module can load without the real SDK
    openai_stub = types.ModuleType("openai")

    class _FakeAsyncOpenAI:
        def __init__(self, **kw: t.Any) -> None:
            self.api_key = kw.get("api_key")
            self.base_url = kw.get("base_url")

    openai_stub.AsyncOpenAI = _FakeAsyncOpenAI  # type: ignore[attr-defined]
    sys.modules.setdefault("openai", openai_stub)

    # Register the module so dataclasses can resolve string annotations
    sys.modules[name] = mod

    exec(code, mod.__dict__)
    return mod


@pytest.fixture()
def llm_provider() -> types.ModuleType:
    return _load_module("llm_provider", TEMPLATE_DIR / "llm_provider.py")


@pytest.fixture()
def conversation_mod() -> types.ModuleType:
    return _load_module("conversation", TEMPLATE_DIR / "conversation.py")


# ---- Unit tests: llm_provider.detect_provider() --------------------------


class TestDetectProvider:
    """Tests for automatic LLM provider detection."""

    def test_no_env_vars_returns_none(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert client is None
            assert config is None

    def test_openai_key_detected(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "sk-test"},
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert client is not None
            assert config is not None
            assert config.provider == "openai"
            assert config.model == "gpt-3.5-turbo"
            assert config.provider_name == "OpenAI"
            assert client.api_key == "sk-test"

    def test_minimax_key_detected(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {"MINIMAX_API_KEY": "mm-test-key"},
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert client is not None
            assert config is not None
            assert config.provider == "minimax"
            assert config.model == "MiniMax-M2.7"
            assert config.provider_name == "MiniMax"
            assert client.api_key == "mm-test-key"
            assert client.base_url == "https://api.minimax.io/v1"

    def test_explicit_provider_selection(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "minimax",
                "MINIMAX_API_KEY": "mm-key",
                "OPENAI_API_KEY": "sk-key",
            },
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert config is not None
            assert config.provider == "minimax"

    def test_openai_has_priority_in_auto_detect(
        self, llm_provider: types.ModuleType
    ) -> None:
        """When both keys exist without explicit provider, OpenAI wins
        (first in PROVIDERS dict)."""
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-key",
                "MINIMAX_API_KEY": "mm-key",
            },
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert config is not None
            assert config.provider == "openai"

    def test_custom_model_override(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "MINIMAX_API_KEY": "mm-key",
                "LLM_MODEL": "MiniMax-M2.7-highspeed",
            },
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert config is not None
            assert config.model == "MiniMax-M2.7-highspeed"

    def test_unknown_provider_falls_back_to_auto(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "nonexistent",
                "MINIMAX_API_KEY": "mm-key",
            },
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert config is not None
            assert config.provider == "minimax"

    def test_explicit_provider_without_key_falls_back(
        self, llm_provider: types.ModuleType
    ) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "minimax",
                "OPENAI_API_KEY": "sk-key",
            },
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            # No MINIMAX_API_KEY, so explicit fails → auto-detect → OpenAI
            assert config is not None
            assert config.provider == "openai"


# ---- Unit tests: LLMConfig -----------------------------------------------


class TestLLMConfig:
    """Tests for the LLMConfig dataclass."""

    def test_fields(self, llm_provider: types.ModuleType) -> None:
        cfg = llm_provider.LLMConfig(
            provider="minimax",
            model="MiniMax-M2.7",
            provider_name="MiniMax",
        )
        assert cfg.provider == "minimax"
        assert cfg.model == "MiniMax-M2.7"
        assert cfg.provider_name == "MiniMax"


# ---- Unit tests: PROVIDERS dict -------------------------------------------


class TestProviderPresets:
    """Verify built-in provider presets are well-formed."""

    def test_providers_dict_has_openai(
        self, llm_provider: types.ModuleType
    ) -> None:
        assert "openai" in llm_provider.PROVIDERS

    def test_providers_dict_has_minimax(
        self, llm_provider: types.ModuleType
    ) -> None:
        assert "minimax" in llm_provider.PROVIDERS

    def test_minimax_base_url(self, llm_provider: types.ModuleType) -> None:
        assert (
            llm_provider.PROVIDERS["minimax"]["base_url"]
            == "https://api.minimax.io/v1"
        )

    def test_minimax_default_model(
        self, llm_provider: types.ModuleType
    ) -> None:
        assert (
            llm_provider.PROVIDERS["minimax"]["default_model"]
            == "MiniMax-M2.7"
        )

    def test_minimax_api_key_env(
        self, llm_provider: types.ModuleType
    ) -> None:
        assert (
            llm_provider.PROVIDERS["minimax"]["api_key_env"]
            == "MINIMAX_API_KEY"
        )

    def test_each_provider_has_required_keys(
        self, llm_provider: types.ModuleType
    ) -> None:
        required = {"name", "base_url", "default_model", "api_key_env"}
        for name, preset in llm_provider.PROVIDERS.items():
            assert required.issubset(
                preset.keys()
            ), f"Provider {name!r} missing keys"


# ---- Unit tests: Conversation ---------------------------------------------


class TestConversation:
    """Tests for the Conversation dataclass."""

    def test_conversation_starts_empty(
        self, conversation_mod: types.ModuleType
    ) -> None:
        conv = conversation_mod.Conversation()
        assert conv.messages == []

    def test_respond_raises_without_user_message(
        self, conversation_mod: types.ModuleType
    ) -> None:
        conv = conversation_mod.Conversation()
        import asyncio

        with pytest.raises(ValueError, match="most recent message"):
            asyncio.get_event_loop().run_until_complete(
                conv.respond(client=None, model="gpt-3.5-turbo")
            )

    def test_respond_without_client_returns_help(
        self, conversation_mod: types.ModuleType
    ) -> None:
        import asyncio
        from datetime import datetime, timezone

        conv = conversation_mod.Conversation()
        conv.messages.append(
            conversation_mod.ChatMessage(
                role="user",
                timestamp=datetime.now(tz=timezone.utc),
                text="Hello",
            )
        )
        msg = asyncio.get_event_loop().run_until_complete(
            conv.respond(client=None, model="MiniMax-M2.7")
        )
        assert msg.role == "assistant"
        assert "API key" in msg.text

    def test_respond_accepts_model_parameter(
        self, conversation_mod: types.ModuleType
    ) -> None:
        """Ensure the respond() method accepts a model parameter."""
        import asyncio
        import inspect

        sig = inspect.signature(conversation_mod.Conversation.respond)
        assert "model" in sig.parameters


# ---- Template structure tests ---------------------------------------------


class TestTemplateStructure:
    """Tests that the template files are well-formed."""

    def test_llm_provider_file_exists(self) -> None:
        assert (TEMPLATE_DIR / "llm_provider.py").is_file()

    def test_root_init_has_sections(self) -> None:
        import re

        content = (TEMPLATE_DIR / "root_init.py").read_text()
        assert "# <additional-imports>" in content
        assert "# </additional-imports>" in content
        assert "# <additional-code>" in content
        assert "# </additional-code>" in content

    def test_root_init_imports_llm_provider(self) -> None:
        content = (TEMPLATE_DIR / "root_init.py").read_text()
        assert "llm_provider" in content

    def test_chat_page_imports_llm_provider(self) -> None:
        content = (TEMPLATE_DIR / "pages" / "chat_page.py").read_text()
        assert "llm_provider" in content

    def test_chat_page_uses_llm_config(self) -> None:
        content = (TEMPLATE_DIR / "pages" / "chat_page.py").read_text()
        assert "LLMConfig" in content

    def test_conversation_accepts_model(self) -> None:
        content = (TEMPLATE_DIR / "conversation.py").read_text()
        assert 'model:' in content or "model=" in content

    def test_conversation_sets_temperature(self) -> None:
        """MiniMax requires temperature > 0; check it's set explicitly."""
        content = (TEMPLATE_DIR / "conversation.py").read_text()
        assert "temperature" in content

    def test_readme_mentions_minimax(self) -> None:
        content = (TEMPLATE_DIR / "README.md").read_text()
        assert "MiniMax" in content

    def test_readme_mentions_minimax_api_key(self) -> None:
        content = (TEMPLATE_DIR / "README.md").read_text()
        assert "MINIMAX_API_KEY" in content

    def test_all_python_files_have_valid_syntax(self) -> None:
        for py_file in TEMPLATE_DIR.rglob("*.py"):
            try:
                ast.parse(py_file.read_text())
            except SyntaxError as exc:
                pytest.fail(f"Syntax error in {py_file.name}: {exc}")


# ---- Integration tests (skipped without API key) --------------------------


MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")


@pytest.mark.skipif(
    not MINIMAX_API_KEY,
    reason="MINIMAX_API_KEY not set",
)
class TestMiniMaxIntegration:
    """Live integration tests against the MiniMax API."""

    def test_minimax_chat_completion(self) -> None:
        """Send a real request to MiniMax via the OpenAI-compat API."""
        import openai

        client = openai.OpenAI(
            api_key=MINIMAX_API_KEY,
            base_url="https://api.minimax.io/v1",
        )
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[{"role": "user", "content": 'Say "test passed"'}],
            max_tokens=20,
            temperature=1.0,
        )
        assert response.choices[0].message.content

    def test_minimax_highspeed_model(self) -> None:
        """Verify the highspeed model variant works."""
        import openai

        client = openai.OpenAI(
            api_key=MINIMAX_API_KEY,
            base_url="https://api.minimax.io/v1",
        )
        response = client.chat.completions.create(
            model="MiniMax-M2.7-highspeed",
            messages=[{"role": "user", "content": 'Say "hello"'}],
            max_tokens=20,
            temperature=1.0,
        )
        assert response.choices[0].message.content

    def test_detect_provider_with_real_key(self) -> None:
        """Ensure detect_provider picks up MiniMax when the key is set."""
        llm_provider = _load_module(
            "llm_provider", TEMPLATE_DIR / "llm_provider.py"
        )
        with mock.patch.dict(
            os.environ,
            {"MINIMAX_API_KEY": MINIMAX_API_KEY or ""},
            clear=True,
        ):
            client, config = llm_provider.detect_provider()
            assert config is not None
            assert config.provider == "minimax"
