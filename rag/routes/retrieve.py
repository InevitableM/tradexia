"""POST /retrieve

Flow: embed query -> vector_store.search(filtered by symbol) -> return top-k chunks + metadata.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from config import get_settings
from embeddings import embed_text
from vector_store import vector_store
from models import RetrieveRequest, RetrieveResponse, RetrievedChunk

router = APIRouter()


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest) -> RetrieveResponse:
    logger.info(f"[retrieve] request received: query={req.query!r} symbol={req.symbol!r} top_k={req.top_k}")

    if not req.query or not req.query.strip():
        logger.warning("[retrieve] rejected: empty query")
        raise HTTPException(status_code=400, detail="query must not be empty")

    settings = get_settings()
    top_k = req.top_k or settings.default_top_k

    # Stage 1: embed the query
    try:
        query_embedding = await embed_text(req.query)
    except Exception as e:
        logger.exception("[retrieve] stage 1/2 failed: embedding query")
        raise HTTPException(status_code=502, detail=f"failed to embed query: {e}")

    logger.info(f"[retrieve] stage 1/2 done: query embedded (dimension={len(query_embedding)})")

    # Stage 2: vector search
    try:
        rows = await vector_store.search(query_embedding, req.symbol, top_k)
    except Exception as e:
        logger.exception("[retrieve] stage 2/2 failed: vector search")
        raise HTTPException(status_code=500, detail=f"failed to search: {e}")

    logger.info(f"[retrieve] stage 2/2 done: {len(rows)} chunk(s) found")

    chunks = [
        RetrievedChunk(
            content=row["content"],
            score=row["score"],
            symbol=row["symbol"],
            doc_type=row["doc_type"],
            title=row["title"],
            source_url=row["source_url"],
        )
        for row in rows
    ]

    return RetrieveResponse(chunks=chunks)
