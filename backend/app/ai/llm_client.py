"""LLM Client - Abstraction layer for Claude and GPT-4.

Provides unified interface for:
- Message generation
- Token counting
- Streaming responses
- Error handling & retries
- Cost tracking
"""

import logging
import time
from typing import AsyncIterator, Optional

from app.config import settings
from app.execution_studio import emit_event

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified client for LLM providers (Claude, OpenAI).

    Abstracts away provider-specific logic so agents can swap models via config.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """Initialize LLM client.

        Args:
            provider: "anthropic" or "openai" (defaults to settings.llm_provider)
            model: Model name (defaults to settings.llm_model)
            api_key: API key (defaults to settings.llm_api_key)
            max_tokens: Max tokens in response (defaults to settings.llm_max_tokens)
            temperature: Sampling temperature (defaults to settings.llm_temperature)
        """
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.temperature = temperature or settings.llm_temperature
        self.timeout = settings.llm_timeout_seconds

        if self.provider == "anthropic":
            try:
                import anthropic

                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package required for Claude models")
        elif self.provider == "openai":
            try:
                import openai

                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required for GPT models")
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        logger.info(f"LLM Client initialized: {self.provider}/{self.model}")

    async def generate(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate LLM response.

        Args:
            messages: List of message dicts {"role": "user|assistant", "content": "..."}
            system_prompt: Optional system prompt to prepend
            max_tokens: Override max tokens
            temperature: Override temperature

        Returns:
            Generated response text

        Raises:
            RuntimeError: If LLM call fails
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        start_time = time.time()

        # Emit event: LLM call starting
        emit_event("LLMClient", "generate_start", metadata={
            "model": self.model,
            "provider": self.provider,
            "max_tokens": max_tokens,
        })

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt or "",
                    messages=messages,
                    timeout=self.timeout,
                )
                result = response.content[0].text

                # Emit event: LLM call succeeded
                elapsed_ms = (time.time() - start_time) * 1000
                emit_event("LLMClient", "generate_complete", metadata={
                    "model": self.model,
                    "provider": self.provider,
                    "latency_ms": elapsed_ms,
                    "result_length": len(result),
                    "tokens_used": getattr(response.usage, 'output_tokens', 0),
                })

                return result

            elif self.provider == "openai":
                messages_copy = messages.copy()
                if system_prompt:
                    messages_copy.insert(0, {"role": "system", "content": system_prompt})

                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages_copy,
                    timeout=self.timeout,
                )
                result = response.choices[0].message.content

                # Emit event: LLM call succeeded
                elapsed_ms = (time.time() - start_time) * 1000
                emit_event("LLMClient", "generate_complete", metadata={
                    "model": self.model,
                    "provider": self.provider,
                    "latency_ms": elapsed_ms,
                    "result_length": len(result),
                    "tokens_used": getattr(response.usage, 'completion_tokens', 0),
                })

                return result

        except Exception as e:
            # Emit event: LLM call failed
            elapsed_ms = (time.time() - start_time) * 1000
            emit_event("LLMClient", "generate_failed",
                      error=str(e),
                      duration_ms=elapsed_ms,
                      metadata={
                          "model": self.model,
                          "provider": self.provider,
                          "error_type": type(e).__name__,
                      })

            logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate LLM response: {e}") from e

    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Stream LLM response tokens.

        Yields tokens as they're generated for real-time UI updates.

        Args:
            messages: List of message dicts
            system_prompt: Optional system prompt
            max_tokens: Override max tokens
            temperature: Override temperature

        Yields:
            Response tokens as strings

        Raises:
            RuntimeError: If stream fails
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            if self.provider == "anthropic":
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt or "",
                    messages=messages,
                    timeout=self.timeout,
                ) as stream:
                    for text in stream.text_stream:
                        yield text

            elif self.provider == "openai":
                messages_copy = messages.copy()
                if system_prompt:
                    messages_copy.insert(0, {"role": "system", "content": system_prompt})

                stream = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages_copy,
                    stream=True,
                    timeout=self.timeout,
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to stream LLM response: {e}") from e

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Simple approximation: ~4 chars per token on average.
        For production, use actual tokenizer from respective library.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough approximation
        return len(text) // 4 + 1

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost of LLM call.

        Args:
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in response

        Returns:
            Estimated cost in USD
        """
        # Placeholder pricing (as of 2024-07)
        # These are rough estimates and should be updated
        if self.provider == "anthropic":
            if "sonnet" in self.model.lower():
                # Claude 3.5 Sonnet: $3/M input, $15/M output
                return (prompt_tokens * 3 + completion_tokens * 15) / 1_000_000
            elif "opus" in self.model.lower():
                # Claude 3 Opus: $15/M input, $75/M output
                return (prompt_tokens * 15 + completion_tokens * 75) / 1_000_000

        elif self.provider == "openai":
            if "gpt-4" in self.model:
                # GPT-4: $30/M input, $60/M output
                return (prompt_tokens * 30 + completion_tokens * 60) / 1_000_000
            elif "gpt-3.5" in self.model:
                # GPT-3.5-turbo: $0.5/M input, $1.5/M output
                return (prompt_tokens * 0.5 + completion_tokens * 1.5) / 1_000_000

        return 0.0
