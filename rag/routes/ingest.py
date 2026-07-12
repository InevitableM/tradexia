"""POST /ingest

Flow: insert document row -> chunk text -> embed chunks (batch) -> store in vector_store.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from config import get_settings
from db import db
from chunker import split_into_chunks
from embeddings import embed_batch
from vector_store import vector_store, ChunkRecord
from models import IngestRequest, IngestResponse

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest) -> IngestResponse:
    logger.info(f"[ingest] request received: symbol={req.symbol} doc_type={req.doc_type} title={req.title!r}")

    if not req.text or not req.text.strip():
        logger.warning("[ingest] rejected: empty text")
        raise HTTPException(status_code=400, detail="text must not be empty")

    settings = get_settings()

    # Stage 1: create the document row
    try:
        row = await db.fetchrow(
            """
            INSERT INTO documents (symbol, doc_type, title, source_url, fiscal_year)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            req.symbol, req.doc_type, req.title, req.source_url, req.fiscal_year,
        )
    except Exception as e:
        logger.exception("[ingest] stage 1/4 failed: creating document row")
        raise HTTPException(status_code=500, detail=f"failed to create document: {e}")

    document_id = str(row["id"])
    logger.info(f"[ingest] stage 1/4 done: document created id={document_id}")

    # Stage 2: chunk the text
    try:
        chunks = split_into_chunks(req.text, settings.chunk_size, settings.chunk_overlap)
    except Exception as e:
        logger.exception(f"[ingest] stage 2/4 failed: chunking text for document_id={document_id}")
        raise HTTPException(status_code=500, detail=f"failed to chunk text: {e}")

    if not chunks:
        logger.warning(f"[ingest] stage 2/4 produced no chunks for document_id={document_id}")
        raise HTTPException(status_code=400, detail="text produced no chunks")

    logger.info(f"[ingest] stage 2/4 done: {len(chunks)} chunk(s) for document_id={document_id}")

    # Stage 3: embed the chunks
    try:
        vectors = await embed_batch(chunks)
    except Exception as e:
        logger.exception(f"[ingest] stage 3/4 failed: embedding {len(chunks)} chunk(s) for document_id={document_id}")
        raise HTTPException(status_code=502, detail=f"failed to generate embeddings: {e}")

    logger.info(f"[ingest] stage 3/4 done: {len(vectors)} embedding(s) for document_id={document_id}")

    # Stage 4: store chunks + embeddings
    records = [
        ChunkRecord(
            document_id=document_id,
            symbol=req.symbol,
            chunk_index=i,
            content=chunk,
            embedding=vector,
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    try:
        await vector_store.add(records)
    except Exception as e:
        logger.exception(f"[ingest] stage 4/4 failed: storing {len(records)} chunk(s) for document_id={document_id}")
        raise HTTPException(status_code=500, detail=f"failed to store chunks: {e}")

    logger.info(f"[ingest] stage 4/4 done: {len(records)} chunk(s) stored — document_id={document_id} complete")

    return IngestResponse(document_id=document_id, chunks_created=len(records))
