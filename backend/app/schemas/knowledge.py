"""知识库相关 Pydantic 模型"""

from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int | None = None
    chunk_count: int = 0
    uploaded_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    content: str
    score: float
    file_id: int | None = None
    filename: str | None = None
    chunk_index: int | None = None


class KnowledgeSearchOut(BaseModel):
    query: str
    results: list[SearchResult]


class KnowledgeAskOut(BaseModel):
    query: str
    answer: str
    sources: list[SearchResult]
