"""Standalone script to sanity-check chunking + embedding generation,
without needing Postgres set up yet.

Usage:
    python test_embeddings.py
"""

import asyncio

from chunker import split_into_chunks
from embeddings import embed_text, embed_batch
from config import get_settings
from google import genai


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)


async def main() -> None:
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)

    # print("Available models:")
    # for model in client.models.list():
    #     print(f"  {model.name}")
    # print("-" * 60)

    with open("sample_docs/tcs_sample.txt", "r", encoding="utf-8") as f:
        text = f.read()

    print(f"Loaded document: {len(text)} characters")

    chunks = split_into_chunks(text, settings.chunk_size, settings.chunk_overlap)
    print(f"Split into {len(chunks)} chunk(s)")
    for i, chunk in enumerate(chunks):
        preview = chunk[:80].replace("\n", " ")
        print(f"  chunk[{i}] ({len(chunk)} chars): {preview}...")

    print("\nEmbedding chunks...")
    vectors = await embed_batch(chunks)
    print(f"Got {len(vectors)} embedding(s), dimension={len(vectors[0])}")

    query = "What are TCS's main sources of revenue?"
    print(f"\nEmbedding query: {query!r}")
    query_vector = await embed_text(query)
    print(f"Query embedding dimension={len(query_vector)}")

    print(
        "\nCosine similarity of query vs each chunk (sanity check — should be highest for the revenue-sources chunk):"
    )
    for i, chunk_vector in enumerate(vectors):
        score = cosine_similarity(query_vector, chunk_vector)
        print(f"  chunk[{i}]: {score:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
