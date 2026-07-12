"""VectorStore abstraction. This is the only file that knows the store is
pgvector — routes/chunker/embeddings never talk to Postgres directly, only
through this interface. Swapping vector stores later means changing only
this file.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

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
            return
        await db.executemany(
            """
            INSERT INTO document_chunks
                (document_id, symbol, chunk_index, content, embedding)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [
                (c.document_id, c.symbol, c.chunk_index, c.content, str(c.embedding))
                for c in chunks
            ],
        )

    async def search(
        self, query_embedding: list[float], symbol: str | None, top_k: int
    ) -> list[dict]:
        # Retrieval is not wired up yet — implemented alongside routes/retrieve.py.
        raise NotImplementedError


# Instantiated once here; the one instance routes/ingest.py imports.
vector_store: VectorStore = PgVectorStore()
