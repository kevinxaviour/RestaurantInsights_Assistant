import os
from typing import Any

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .config import AssistantConfig


class ProviderError(RuntimeError):
    pass


class LLMProviderRouter:
    """OpenAI primary, then Groq, then OpenRouter."""

    def __init__(self, config: AssistantConfig):
        self.config = config

    def _provider_chain(self) -> list[tuple[str, Any]]:
        provider_map: dict[str, Any] = {}

        if os.getenv("OPENAI_API_KEY"):
            provider_map["openai"] = ChatOpenAI(
                model=self.config.openai_model, temperature=0
            )

        if os.getenv("GROQ_API_KEY"):
            provider_map["groq"] = ChatGroq(model=self.config.groq_model, temperature=0)

        if os.getenv("OPENROUTER_API_KEY"):
            provider_map["openrouter"] = ChatOpenAI(
                model=self.config.openrouter_model,
                temperature=0,
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )

        default_order = ["openai", "groq", "openrouter"]
        preferred = self.config.preferred_provider.strip().lower()
        ordered_names = [name for name in default_order if name != preferred]
        ordered_names.insert(0, preferred)

        providers: list[tuple[str, Any]] = []
        for provider_name in ordered_names:
            if provider_name in provider_map:
                providers.append((provider_name, provider_map[provider_name]))

        return providers

    def invoke_structured(
        self, prompt: str, schema: type[BaseModel]
    ) -> tuple[str, BaseModel]:
        errors: list[str] = []

        for provider_name, llm in self._provider_chain():
            try:
                response = llm.with_structured_output(schema).invoke(prompt)
                return provider_name, response
            except Exception as exc:  # pragma: no cover
                errors.append(f"{provider_name}: {exc}")

        raise ProviderError("All providers failed. " + " | ".join(errors))
