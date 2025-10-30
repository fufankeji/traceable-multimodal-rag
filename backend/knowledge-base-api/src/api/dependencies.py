from fastapi import Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.knowledge_base_service import KnowledgeBaseService
from ..services.file_service import FileService
from ..services.chunk_service import ChunkService
from ..services.vector_service import VectorService

def get_knowledge_base_service(db: Session = Depends(get_db)) -> KnowledgeBaseService:
    return KnowledgeBaseService(db)

def get_file_service(db: Session = Depends(get_db)) -> FileService:
    return FileService(db)

def get_chunk_service(db: Session = Depends(get_db)) -> ChunkService:
    return ChunkService(db)

def get_vector_service(db: Session = Depends(get_db)) -> VectorService:
    return VectorService(db)