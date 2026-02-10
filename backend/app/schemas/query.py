from pydantic import BaseModel
from datetime import datetime

class QueryCreate(BaseModel):
    query: str

class QueryResponse(BaseModel):
    id: int
    query: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True

class RAGRequest(BaseModel):
    question: str
    top_k: int = 5

class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    query_id: int
