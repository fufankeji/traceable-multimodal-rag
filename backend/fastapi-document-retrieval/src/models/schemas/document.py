from pydantic import BaseModel
from typing import List, Optional

class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_count: int

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int

    class Config:
        orm_mode = True

class DocumentResponse(BaseModel):
    filename: str
    unique_id: int
    status: str

class DocumentListResponse(BaseModel):
    documents: List[Document]