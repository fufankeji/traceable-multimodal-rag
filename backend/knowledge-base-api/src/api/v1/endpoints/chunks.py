from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from src.crud.chunks import create_chunk, get_chunk, delete_chunk
from src.schemas.chunks import ChunkCreate, ChunkResponse

router = APIRouter()

class UploadResponse(BaseModel):
    filename: str
    id: str
    status: str

@router.post("/chunks/", response_model=UploadResponse)
async def upload_chunk(file: UploadFile = File(...)):
    try:
        chunk_data = await file.read()
        chunk_id = create_chunk(file.filename, chunk_data)  # Assuming create_chunk returns the ID of the created chunk
        return UploadResponse(filename=file.filename, id=chunk_id, status="uploaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunks/{chunk_id}", response_model=ChunkResponse)
async def read_chunk(chunk_id: str):
    chunk = get_chunk(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk

@router.delete("/chunks/{chunk_id}", response_model=dict)
async def remove_chunk(chunk_id: str):
    success = delete_chunk(chunk_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"detail": "Chunk deleted successfully"}