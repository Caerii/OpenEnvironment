"""Abstractions over different LLM providers (Cerebras, Together, etc.)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from cerebras.cloud.sdk import Cerebras

try:
    from together import Together  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Together = None

try:
    from google import genai  # type: ignore
    from google.genai import types as genai_types  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    genai = None
    genai_types = None

logger = logging.getLogger(__name__)


class LLMClient:
    """Base class for chat-based LLM clients."""

    provider: str

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
    ) -> Any:
        raise NotImplementedError

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Any:
        raise NotImplementedError


class CerebrasLLMClient(LLMClient):
    """Wrapper around the Cerebras chat completions API."""

    def __init__(self, api_key: str, model: str) -> None:
        self.provider = "cerebras"
        self.model = model
        self._client = Cerebras(api_key=api_key)

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
    ) -> Any:
        params: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice or "auto",
            temperature=temperature,
            parallel_tool_calls=True,
        )
        if top_p is not None:
            params["top_p"] = top_p
        if max_completion_tokens is not None:
            params["max_completion_tokens"] = max_completion_tokens
        return self._client.chat.completions.create(**params)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if top_p is not None:
            params["top_p"] = top_p
        if max_completion_tokens is not None:
            params["max_completion_tokens"] = max_completion_tokens
        if response_format is not None:
            params["response_format"] = response_format
        return self._client.chat.completions.create(**params)


class TogetherLLMClient(LLMClient):
    """Wrapper around Together.ai's OpenAI-compatible chat API."""

    def __init__(self, api_key: str, model: str) -> None:
        if Together is None:  # pragma: no cover - handled by dependency declaration
            raise RuntimeError("together package is required for Together client")
        self.provider = "together"
        self.model = model
        self._client = Together(api_key=api_key)

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        if top_p is not None:
            params["top_p"] = top_p
        if max_completion_tokens is not None:
            params["max_tokens"] = max_completion_tokens
        return self._client.chat.completions.create(**params)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if top_p is not None:
            params["top_p"] = top_p
        if max_completion_tokens is not None:
            params["max_tokens"] = max_completion_tokens
        if response_format is not None:
            params["response_format"] = response_format
        return self._client.chat.completions.create(**params)


class GeminiLLMClient(LLMClient):
    """Wrapper around Google Gemini chat API (text-only for now)."""

    def __init__(self, api_key: str, model: str) -> None:
        if genai is None:  # pragma: no cover - handled by dependency declaration
            raise RuntimeError("google-genai package is required for Gemini client")
        self.provider = "gemini"
        self.model = model
        self._client = genai.Client(api_key=api_key)

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
    ) -> Any:
        raise NotImplementedError("Gemini tool-calling integration is not yet implemented")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Any:
        prompt = self._concat_messages(messages)

        generation_config = genai_types.GenerationConfig(
            temperature=temperature,
            top_p=top_p if top_p is not None else 0.95,
            max_output_tokens=max_completion_tokens or 2048,
        )

        response = self._client.responses.generate(
            model=self.model,
            input=prompt,
            config=generation_config,
        )

        text = getattr(response, "output_text", None)
        if not text and getattr(response, "candidates", None):
            candidate = response.candidates[0]
            text = getattr(candidate, "output_text", "")

        return _wrap_text_response(text or "")

    def _concat_messages(self, messages: List[Dict[str, Any]]) -> str:
        formatted: List[str] = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)


def _wrap_text_response(text: str) -> Any:
    class Message:
        def __init__(self, content: str) -> None:
            self.content = content

    class Choice:
        def __init__(self, content: str) -> None:
            self.message = Message(content)

    class Response:
        def __init__(self, content: str) -> None:
            self.choices = [Choice(content)]

    return Response(text)
