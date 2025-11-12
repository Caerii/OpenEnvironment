"""Factory helpers for creating LLM clients based on environment configuration."""

from __future__ import annotations

import os
import logging
from typing import Optional

from .clients import LLMClient, CerebrasLLMClient, TogetherLLMClient, GeminiLLMClient

logger = logging.getLogger(__name__)


# Model recommendations:
# - For Cerebras: Use larger models if available (qwen-3-32b, gpt-oss-120b)
# - For Together: llama-3.3-70b (65k context) or qwen-3-32b (65k context) recommended
# - For Gemini Visual Critique: gemini-2.5-flash-image (images+text input/output, image generation, 65k context)
# - For Gemini Reasoning: gemini-2.5-pro (1M context, function calling, thinking) - optional alternative to Together
# - Current llama3.1-8b has only 8k context - limiting for complex ReAct workflows
DEFAULT_CEREBRAS_MODEL = "llama3.1-8b"  # Default Cerebras model (70b not available, using 8b)
DEFAULT_TOGETHER_MODEL = "llama-3.3-70b"  # Updated: 65k context, better for ReAct
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-image"  # Images+text, image generation, 65k context - PERFECT for visual critique
DEFAULT_GEMINI_PRO_MODEL = "gemini-2.5-pro"  # 1M context, function calling, thinking - for complex reasoning


def create_llm_client() -> Optional[LLMClient]:
    provider = os.environ.get("LLM_PROVIDER", "cerebras").strip().lower()

    if provider == "cerebras":
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            logger.warning("CEREBRAS_API_KEY not set; LLM features will be disabled")
            return None
        model = os.environ.get("CEREBRAS_MODEL", DEFAULT_CEREBRAS_MODEL)
        return CerebrasLLMClient(api_key, model)

    if provider == "together":
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            logger.warning("TOGETHER_API_KEY not set; LLM features will be disabled")
            return None
        model = os.environ.get("TOGETHER_MODEL", DEFAULT_TOGETHER_MODEL)
        try:
            return TogetherLLMClient(api_key, model)
        except RuntimeError as exc:
            logger.error(f"Failed to initialise Together client: {exc}")
            return None

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set; LLM features will be disabled")
            return None
        model = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        try:
            return GeminiLLMClient(api_key, model)
        except RuntimeError as exc:
            logger.error(f"Failed to initialise Gemini client: {exc}")
            return None

    logger.error(f"Unknown LLM provider '{provider}' configured")
    return None
