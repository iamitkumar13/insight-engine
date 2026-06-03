"""LLM provider abstraction. Supports Hugging Face Inference API and Anthropic."""
from __future__ import annotations

import os
from typing import Protocol


class LLMProvider(Protocol):
    name: str

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str: ...


class HFProvider:
    name = "hf"

    def __init__(self, model: str, token: str) -> None:
        from huggingface_hub import InferenceClient

        self.model = model
        self.client = InferenceClient(model=model, token=token)

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        out = self.client.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return out.choices[0].message.content or ""


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            b.text for b in msg.content if getattr(b, "type", None) == "text"
        )


def get_llm() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "hf").lower()
    if provider == "hf":
        token = os.getenv("HF_TOKEN")
        model = os.getenv("HF_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct")
        if not token:
            raise RuntimeError("HF_TOKEN is required when LLM_PROVIDER=hf")
        return HFProvider(model=model, token=token)
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicProvider(api_key=key, model=model)
    raise RuntimeError(
        f"Unknown LLM_PROVIDER: {provider!r} (expected 'hf' or 'anthropic')"
    )
