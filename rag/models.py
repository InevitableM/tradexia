"""Pydantic request/response schemas."""

from pydantic import BaseModel


class IngestRequest(BaseModel):
    symbol: str
    doc_type: str
    title: str
    source_url: str | None = None
    fiscal_year: str | None = None
    text: str


class IngestResponse(BaseModel):
    document_id: str
    chunks_created: int


class RetrieveRequest(BaseModel):
    query: str
    symbol: str | None = None
    top_k: int | None = None  # falls back to settings.default_top_k if unset


class RetrievedChunk(BaseModel):
    content: str
    score: float
    symbol: str
    doc_type: str
    title: str | None
    source_url: str | None


class RetrieveResponse(BaseModel):
    chunks: list[RetrievedChunk]
