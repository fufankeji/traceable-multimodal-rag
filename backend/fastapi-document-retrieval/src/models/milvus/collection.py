from pydantic import BaseModel
from typing import List, Optional

class MilvusCollection(BaseModel):
    chunk_text: str
    file_name: str
    unique_id: str
    dense_vector: List[float]
    metadata: Optional[dict] = None

    class Config:
        orm_mode = True