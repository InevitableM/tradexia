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
