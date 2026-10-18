from dataclasses import dataclass, field

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Page:
    number: int
    text: str


@dataclass(frozen=True)
class Document:
    id: str
    name: str
    sha256: str
    mime_type: str
    created_at: str
    pages: tuple[Page, ...]
    data: bytes = field(repr=False)


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    filename: str
    page: int
    text: str


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    document_ids: list[str] | None = Field(default=None, max_length=40)
    top_k: int = Field(default=4, ge=1, le=6)


class GroundedCitation(BaseModel):
    source_id: str = Field(description="Source label, such as S1, from the supplied context.")
    quote: str = Field(min_length=8, max_length=800, description="Exact supporting source quote.")


class GroundedAnswer(BaseModel):
    answer: str = Field(max_length=6000)
    insufficient_evidence: bool
    citations: list[GroundedCitation] = Field(max_length=6)
