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
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    settings = get_settings()

    row = await db.fetchrow(
        """
        INSERT INTO documents (symbol, doc_type, title, source_url, fiscal_year)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        req.symbol, req.doc_type, req.title, req.source_url, req.fiscal_year,
    )
    document_id = str(row["id"])
    logger.info(f"[ingest] document created id={document_id} symbol={req.symbol}")

    chunks = split_into_chunks(req.text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise HTTPException(status_code=400, detail="text produced no chunks")

    vectors = await embed_batch(chunks)

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
    await vector_store.add(records)
    logger.info(f"[ingest] {len(records)} chunks stored for document_id={document_id}")

    return IngestResponse(document_id=document_id, chunks_created=len(records))
