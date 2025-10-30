from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from models.schemas.document import DocumentCreate, DocumentResponse
from services.document_service import DocumentService

router = APIRouter()
document_service = DocumentService()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db_name: str = ""):
    if not db_name:
        raise HTTPException(status_code=400, detail="Database name is required")
    
    content = await file.read()
    filename = file.filename
    unique_id = document_service.upload_document(content, filename, db_name)
    
    return DocumentResponse(filename=filename, unique_id=unique_id, status="Uploaded successfully")

@router.get("/{unique_id}", response_model=DocumentResponse)
async def get_document(unique_id: str):
    document = document_service.get_document(unique_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@router.delete("/{unique_id}", response_model=dict)
async def delete_document(unique_id: str):
    success = document_service.delete_document(unique_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"status": "Deleted successfully"}