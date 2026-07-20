"""VectorStore abstraction. This is the only file that knows the store is
pgvector — routes/chunker/embeddings never talk to Postgres directly, only
through this interface. Swapping vector stores later means changing only
this file.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from loguru import logger
from db import db


@dataclass
class ChunkRecord:
    document_id: str
    symbol: str
    chunk_index: int
    content: str
    embedding: list[float]


class VectorStore(ABC):
    @abstractmethod
    async def add(self, chunks: list[ChunkRecord]) -> None: ...

    @abstractmethod
    async def search(
        self, query_embedding: list[float], symbol: str | None, top_k: int
    ) -> list[dict]: ...


class PgVectorStore(VectorStore):
    async def add(self, chunks: list[ChunkRecord]) -> None:
        if not chunks:
            logger.warning("[vector_store] add() called with no chunks, skipping")
            return
        logger.info(
            f"[vector_store] inserting {len(chunks)} chunk(s) into document_chunks"
        )
        # db.executemany already logs + reraises on failure — no need to
        # duplicate that here.
        await db.executemany(
            """
            INSERT INTO document_chunks
                (document_id, symbol, chunk_index, content, embedding)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [
                (c.document_id, c.symbol, c.chunk_index, c.content, c.embedding)
                for c in chunks
            ],
        )
        logger.info(f"[vector_store] insert complete ({len(chunks)} chunk(s))")

    async def search(
        self, query_embedding: list[float], symbol: str | None, top_k: int
    ) -> list[dict]:
        logger.info(f"[vector_store] search: symbol={symbol!r} top_k={top_k}")

        # pgvector's <=> operator is cosine distance (0 = identical, 2 = opposite);
        # similarity = 1 - distance, so ORDER BY the raw operator ranks nearest first.
        if symbol:
            rows = await db.fetch(
                """
                SELECT c.content, c.symbol,
                       d.doc_type, d.title, d.source_url,
                       1 - (c.embedding <=> $1) AS score
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.symbol = $2
                ORDER BY c.embedding <=> $1
                LIMIT $3
                """,
                query_embedding,
                symbol,
                top_k,
            )
        else:
            rows = await db.fetch(
                """
                SELECT c.content, c.symbol,
                       d.doc_type, d.title, d.source_url,
                       1 - (c.embedding <=> $1) AS score
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                ORDER BY c.embedding <=> $1
                LIMIT $2
                """,
                query_embedding,
                top_k,
            )

        logger.info(f"[vector_store] search ← {len(rows)} result(s)")
        return [dict(row) for row in rows]


# Instantiated once here; the one instance routes/ingest.py imports.
vector_store: VectorStore = PgVectorStore()
