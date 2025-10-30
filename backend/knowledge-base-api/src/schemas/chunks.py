from pydantic import BaseModel
from typing import List, Optional

class ChunkBase(BaseModel):
    text: str
    page_start: int
    page_end: int
    is_table_like: Optional[bool] = False

class ChunkCreate(ChunkBase):
    pass

class Chunk(ChunkBase):
    id: int

    class Config:
        orm_mode = True

class ChunkResponse(BaseModel):
    filename: str
    unique_id: int
    upload_status: str

class ChunkListResponse(BaseModel):
    chunks: List[Chunk]