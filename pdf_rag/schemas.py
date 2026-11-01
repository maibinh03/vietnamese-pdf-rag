from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    sha256: str
    chunk_count: int
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int | None
    chunk_index: int
    char_start: int
    char_end: int
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    abstained: bool
    citations: list[Citation]
    retrieval_latency_ms: float
    generation_latency_ms: float


class HealthResponse(BaseModel):
    status: str
    vector_store: str
    llm: str

