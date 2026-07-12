"""Pure text-splitting logic — no I/O, no external calls.

Splits raw document text into overlapping, token-sized chunks suitable for
embedding. Token-aware (via tiktoken) rather than naive character counting,
since chunk_size/chunk_overlap are specified in tokens.
"""
import tiktoken
from loguru import logger

# cl100k_base is a reasonable general-purpose tokenizer for length estimation;
# it doesn't need to exactly match Gemini's own tokenizer — it's only used to
# size chunks consistently, not for billing/exact token counts.
_ENCODING = tiktoken.get_encoding("cl100k_base")


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split `text` into chunks of ~chunk_size tokens, with `overlap` tokens
    repeated between consecutive chunks so ideas spanning a chunk boundary
    aren't lost from both sides.
    """
    if not text or not text.strip():
        logger.warning("[chunker] received empty text, returning no chunks")
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    tokens = _ENCODING.encode(text)
    logger.info(f"[chunker] encoded {len(text)} chars → {len(tokens)} tokens (chunk_size={chunk_size}, overlap={overlap})")

    if len(tokens) <= chunk_size:
        logger.info("[chunker] text fits in a single chunk")
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _ENCODING.decode(chunk_tokens).strip()
        if chunk_text:
            chunks.append(chunk_text)
        if end == len(tokens):
            break
        start += step

    logger.info(f"[chunker] produced {len(chunks)} chunk(s)")
    return chunks
