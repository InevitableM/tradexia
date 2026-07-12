"""Wraps Gemini's embedding API. This is the single place that knows which
embedding model is in use — ingestion and retrieval both go through here so
query and chunk vectors always come from the same model/dimensionality.
"""
from google import genai
from config import get_settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.google_api_key)
    return _client


async def embed_text(text: str) -> list[float]:
    """Embed a single piece of text (typically a user's query)."""
    settings = get_settings()
    result = await _get_client().aio.models.embed_content(
        model=settings.embedding_model,
        contents=text,
    )
    return result.embeddings[0].values


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple chunks in as few API calls as possible (ingestion)."""
    if not texts:
        return []
    settings = get_settings()
    result = await _get_client().aio.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
    )
    return [e.values for e in result.embeddings]
