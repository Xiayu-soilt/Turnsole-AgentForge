from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm(temperature: float = 0.7, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        timeout=120,
    )
