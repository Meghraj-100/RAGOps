"""LLM client — Groq via OpenAI-compatible SDK."""

from openai import AsyncOpenAI
from app.core.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


async def generate(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> tuple[str, dict]:
    """
    Generate a response from the LLM.
    Returns (text, usage_dict).
    """
    client = _get_client()
    temp = temperature if temperature is not None else settings.llm_temperature
    max_tok = max_tokens if max_tokens is not None else settings.llm_max_tokens

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temp,
            max_tokens=max_tok,
        )
        text = response.choices[0].message.content or ""
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return text, usage
    except Exception as e:
        logger.error("llm_generation_failed", error=str(e))
        raise
