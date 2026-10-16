from typing import Protocol

from app.core.config import Settings


class LLMError(Exception):
    pass


class LLMProvider(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class GroqProvider:
    def __init__(self, settings: Settings):
        if not settings.groq_api_key or not settings.groq_model:
            raise LLMError("GROQ_API_KEY and GROQ_MODEL must be set.")
        from groq import Groq

        self._client = Groq(api_key=settings.groq_api_key, timeout=30, max_retries=1)
        self._model = settings.groq_model

    def complete(self, system: str, user: str) -> str:
        try:
            r = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
            return r.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"LLM provider error: {type(e).__name__}") from e


def get_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "groq":
        return GroqProvider(settings)
    raise LLMError(f"Unsupported LLM_PROVIDER '{settings.llm_provider}'.")
