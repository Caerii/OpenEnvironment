"""LLM configuration helpers for AG2 multi-agent workflows."""

from __future__ import annotations

import os
from typing import Any, Dict


DEFAULT_CEREBRAS_MODEL = "llama3.1-8b"
DEFAULT_TOGETHER_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-image"  # Updated: Images + text, image generation, 65k context


PROFILE_DEFAULTS = {
    "compact": {"temperature": 0.35, "top_p": 0.85, "max_completion_tokens": 1800},
    "standard": {"temperature": 0.4, "top_p": 0.9, "max_completion_tokens": 3200},
    "extended32k": {"temperature": 0.45, "top_p": 0.92, "max_completion_tokens": 8000},
    "omni": {"temperature": 0.5, "top_p": 0.95, "max_completion_tokens": 12000},
}


def build_llm_config(profile: str | None = None) -> Dict[str, Any]:
    """Return an AG2-compatible llm_config dictionary based on environment settings."""

    provider = os.environ.get("LLM_PROVIDER", "together").strip().lower()
    profile = profile or os.environ.get("LLM_PROMPT_PROFILE", "compact")
    profile_defaults = PROFILE_DEFAULTS.get(profile, PROFILE_DEFAULTS["compact"])

    config_list: list[Dict[str, Any]] = []

    if provider == "together":
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            raise RuntimeError("TOGETHER_API_KEY must be set for Together provider")
        model = os.environ.get("TOGETHER_MODEL", DEFAULT_TOGETHER_MODEL)
        config_list.append(
            {
                "api_type": "together",
                "model": model,
                "api_key": api_key,
            }
        )

    elif provider == "cerebras":
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise RuntimeError("CEREBRAS_API_KEY must be set for Cerebras provider")
        model = os.environ.get("CEREBRAS_MODEL", DEFAULT_CEREBRAS_MODEL)
        config_list.append(
            {
                "api_type": "cerebras",
                "model": model,
                "api_key": api_key,
            }
        )

    elif provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY must be set for Gemini provider")
        model = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        config_list.append(
            {
                "api_type": "gemini",
                "model": model,
                "api_key": api_key,
            }
        )
    else:
        raise RuntimeError(f"Unknown LLM provider '{provider}'")

    llm_config: Dict[str, Any] = {
        "config_list": config_list,
        "temperature": profile_defaults["temperature"],
        "top_p": profile_defaults["top_p"],
        "max_tokens": profile_defaults["max_completion_tokens"],
        "timeout": int(os.environ.get("LLM_TIMEOUT", "120")),
    }

    return llm_config
