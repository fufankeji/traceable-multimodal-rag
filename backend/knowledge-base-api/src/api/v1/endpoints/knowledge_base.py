from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from src.crud.knowledge_base import create_knowledge_base, delete_knowledge_base, get_knowledge_base
from src.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse

router = APIRouter()

class UploadResponse(BaseModel):
    filename: str
    id: str
    status: str

@router.post("/knowledge_base/", response_model=UploadResponse)
async def upload_knowledge_base(
    knowledge_base: KnowledgeBaseCreate
):
    try:
        knowledge_base_id = create_knowledge_base(knowledge_base)
        return UploadResponse(
            filename=knowledge_base.name,
            id=knowledge_base_id,
            status="uploaded"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/knowledge_base/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def read_knowledge_base(knowledge_base_id: str):
    knowledge_base = get_knowledge_base(knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return knowledge_base

@router.delete("/knowledge_base/{knowledge_base_id}", response_model=UploadResponse)
async def delete_knowledge_base_endpoint(knowledge_base_id: str):
    try:
        delete_knowledge_base(knowledge_base_id)
        return UploadResponse(
            filename="",
            id=knowledge_base_id,
            status="deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))