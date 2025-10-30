from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    limit: int = 10
    offset: int = 0

class SearchResponse(BaseModel):
    total: int
    results: List[dict]