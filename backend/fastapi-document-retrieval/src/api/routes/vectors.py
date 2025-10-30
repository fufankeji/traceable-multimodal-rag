from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from core.milvus_client import MilvusClient
from services.vector_service import VectorService

router = APIRouter()
vector_service = VectorService()

class VectorUploadRequest(BaseModel):
    vector: List[float]
    metadata: dict

class VectorResponse(BaseModel):
    id: str
    status: str

@router.post("/vectors/upload", response_model=VectorResponse)
async def upload_vector(request: VectorUploadRequest):
    try:
        vector_id = await vector_service.upload_vector(request.vector, request.metadata)
        return VectorResponse(id=vector_id, status="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))