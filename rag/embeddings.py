"""Wraps Gemini's embedding API. This is the single place that knows which
embedding model is in use — ingestion and retrieval both go through here so
query and chunk vectors always come from the same model/dimensionality.

gemini-embedding-001 defaults to 3072 dimensions but supports truncated
output via Matryoshka Representation Learning (768/1536/3072 are the
officially supported tiers). Unlike the newer gemini-embedding-2, this model
does NOT auto-normalize truncated vectors — we must L2-normalize manually or
cosine similarity comparisons will be subtly wrong.
"""

import math

from google import genai
from google.genai import types
from loguru import logger
from config import get_settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        logger.info("[embeddings] initializing Gemini client")
        _client = genai.Client(api_key=settings.google_api_key)
    return _client


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


async def embed_text(text: str) -> list[float]:
    """Embed a single piece of text (typically a user's query)."""
    settings = get_settings()
    logger.info(
        f"[embeddings] embed_text → {len(text)} chars, model={settings.embedding_model}, dim={settings.embedding_dimension}"
    )
    try:
        result = await _get_client().aio.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimension
            ),
        )
    except Exception:
        logger.exception("[embeddings] embed_text failed")
        raise
    vector = _l2_normalize(result.embeddings[0].values)
    logger.info(f"[embeddings] embed_text ← dimension={len(vector)}")
    return vector


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple chunks in as few API calls as possible (ingestion)."""
    if not texts:
        logger.warning("[embeddings] embed_batch called with no texts")
        return []
    settings = get_settings()
    logger.info(
        f"[embeddings] embed_batch → {len(texts)} chunk(s), model={settings.embedding_model}, dim={settings.embedding_dimension}"
    )
    try:
        result = await _get_client().aio.models.embed_content(
            model=settings.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimension
            ),
        )
    except Exception:
        logger.exception(f"[embeddings] embed_batch failed for {len(texts)} chunk(s)")
        raise
    vectors = [_l2_normalize(e.values) for e in result.embeddings]
    logger.info(f"[embeddings] embed_batch ← {len(vectors)} vector(s)")
    return vectors
