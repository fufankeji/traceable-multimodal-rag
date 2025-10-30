from sqlalchemy.orm import Session
from fastapi import HTTPException
from schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse
from crud.knowledge_base import create_knowledge_base, get_knowledge_base, delete_knowledge_base
from db.sql.models import KnowledgeBase

class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, knowledge_base: KnowledgeBaseCreate) -> KnowledgeBaseResponse:
        db_knowledge_base = create_knowledge_base(self.db, knowledge_base)
        return KnowledgeBaseResponse(
            id=db_knowledge_base.id,
            name=db_knowledge_base.name,
            status="uploaded"
        )

    def read(self, knowledge_base_id: int) -> KnowledgeBaseResponse:
        db_knowledge_base = get_knowledge_base(self.db, knowledge_base_id)
        if db_knowledge_base is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return KnowledgeBaseResponse(
            id=db_knowledge_base.id,
            name=db_knowledge_base.name,
            status="found"
        )

    def delete(self, knowledge_base_id: int) -> dict:
        success = delete_knowledge_base(self.db, knowledge_base_id)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"status": "deleted", "id": knowledge_base_id}