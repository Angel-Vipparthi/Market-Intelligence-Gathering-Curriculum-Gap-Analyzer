"""Shared LLM factory for agent nodes — routes through OpenRouter."""

from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm(model: str | None = None, temperature: float = 0) -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at OpenRouter.

    OpenRouter is OpenAI-compatible, so ChatOpenAI works with a custom base_url.
    """
    return ChatOpenAI(
        model=model or settings.primary_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=temperature,
        max_tokens=4096,
    )
