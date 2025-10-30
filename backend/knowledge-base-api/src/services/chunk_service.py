from sqlalchemy.orm import Session
from fastapi import HTTPException
from schemas.chunks import ChunkCreate, ChunkResponse
from crud.chunks import create_chunk, get_chunk, delete_chunk
from db.sql.models import Chunk

class ChunkService:
    def __init__(self, db: Session):
        self.db = db

    def store_chunk(self, chunk_data: ChunkCreate) -> ChunkResponse:
        chunk = create_chunk(self.db, chunk_data)
        return ChunkResponse(id=chunk.id, filename=chunk.filename, status="uploaded")

    def retrieve_chunk(self, chunk_id: int) -> ChunkResponse:
        chunk = get_chunk(self.db, chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return ChunkResponse(id=chunk.id, filename=chunk.filename, status="retrieved")

    def remove_chunk(self, chunk_id: int) -> dict:
        deleted = delete_chunk(self.db, chunk_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return {"status": "deleted", "id": chunk_id}