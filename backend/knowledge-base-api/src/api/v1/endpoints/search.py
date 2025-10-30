from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src.services.vector_service import VectorService

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int

class SearchResponse(BaseModel):
    id: str
    filename: str
    score: float

@router.post("/search", response_model=List[SearchResponse])
async def search_vectors(request: SearchRequest):
    try:
        results = VectorService.search(request.query, request.top_k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))