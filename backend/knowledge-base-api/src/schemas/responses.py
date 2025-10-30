from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    filename: str
    unique_id: str
    status: str

class DeleteResponse(BaseModel):
    unique_id: str
    status: str

class SearchResponse(BaseModel):
    results: list
    total: int

class ChunkResponse(BaseModel):
    chunk_id: str
    content: str
    status: str

class KnowledgeBaseResponse(BaseModel):
    unique_id: str
    title: str
    description: Optional[str] = None
    status: str