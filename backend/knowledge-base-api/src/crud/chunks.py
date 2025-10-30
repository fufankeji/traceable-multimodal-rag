from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
from ..db.sql.models import Chunk
from ..schemas.chunks import ChunkCreate, ChunkResponse

def create_chunk(db: Session, chunk: ChunkCreate) -> ChunkResponse:
    db_chunk = Chunk(**chunk.dict())
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return ChunkResponse(id=db_chunk.id, filename=db_chunk.filename, status="uploaded")

def get_chunk(db: Session, chunk_id: int) -> ChunkResponse:
    db_chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if db_chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return ChunkResponse(id=db_chunk.id, filename=db_chunk.filename, status="found")

def delete_chunk(db: Session, chunk_id: int) -> dict:
    db_chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if db_chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    db.delete(db_chunk)
    db.commit()
    return {"detail": "Chunk deleted successfully"}

def get_chunks(db: Session, skip: int = 0, limit: int = 10) -> List[ChunkResponse]:
    chunks = db.query(Chunk).offset(skip).limit(limit).all()
    return [ChunkResponse(id=chunk.id, filename=chunk.filename, status="found") for chunk in chunks]