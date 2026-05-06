"""LLM client abstraction with provider and offline fallback support."""

from dataclasses import dataclass
from typing import Any

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.observability.tracing import configure_langsmith, is_langsmith_enabled


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client with deterministic fallback output."""

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self.model = model or settings.openai_model
        self.api_key = settings.openai_api_key
        self._client: Any | None = None
        if self.api_key:
            self._client = self._build_openai_client()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion from OpenAI when configured, else fallback locally."""

        if self.api_key:
            try:
                return self._complete_with_openai(system_prompt, user_prompt)
            except Exception:
                return self._complete_offline(system_prompt, user_prompt)
        return self._complete_offline(system_prompt, user_prompt)

    def _complete_with_openai(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if self._client is None:
            self._client = self._build_openai_client()
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        usage: Any = response.usage
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)
        cost = self._estimate_cost(input_tokens, output_tokens)
        return LLMResponse(
            content=content.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def _complete_offline(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        prompt = f"{system_prompt}\n\n{user_prompt}".strip()
        sentences = [segment.strip() for segment in prompt.replace("\n", " ").split(".") if segment.strip()]
        summary = ". ".join(sentences[:3]).strip()
        if not summary:
            summary = "No prompt content was provided."
        content = (
            "Offline fallback response generated from local heuristics.\n"
            f"Summary: {summary}.\n"
            "Actionable view: prioritize evidence-backed claims, make trade-offs explicit, "
            "and keep the answer concise and source-aware."
        )
        input_tokens = max(1, len(prompt) // 4)
        output_tokens = max(1, len(content) // 4)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
        )

    def _build_openai_client(self) -> Any:
        from openai import OpenAI

        client: Any = OpenAI(api_key=self.api_key)
        if is_langsmith_enabled():
            from langsmith.wrappers import wrap_openai

            configure_langsmith()
            client = wrap_openai(client)
        return client

    def _estimate_cost(
        self,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> float | None:
        if input_tokens is None or output_tokens is None:
            return None
        pricing = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4.1-mini": (0.40, 1.60),
        }
        input_rate, output_rate = pricing.get(self.model, (0.50, 1.50))
        return round((input_tokens / 1_000_000 * input_rate) + (output_tokens / 1_000_000 * output_rate), 6)
