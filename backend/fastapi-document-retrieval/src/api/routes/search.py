from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.schemas.search import SearchRequest, SearchResponse
from services.search_service import SearchService

router = APIRouter()
search_service = SearchService()

@router.get("/search", response_model=List[SearchResponse])
async def search_documents(request: SearchRequest):
    results = await search_service.search_documents(request)
    if not results:
        raise HTTPException(status_code=404, detail="No documents found")
    return results