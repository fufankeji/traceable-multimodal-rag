from sqlalchemy.orm import Session
from typing import List, Optional
from src.db.sql.models import KnowledgeBase
from src.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate

def create_knowledge_base(db: Session, knowledge_base: KnowledgeBaseCreate) -> KnowledgeBase:
    db_knowledge_base = KnowledgeBase(**knowledge_base.dict())
    db.add(db_knowledge_base)
    db.commit()
    db.refresh(db_knowledge_base)
    return db_knowledge_base

def get_knowledge_base(db: Session, knowledge_base_id: int) -> Optional[KnowledgeBase]:
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()

def get_knowledge_bases(db: Session, skip: int = 0, limit: int = 10) -> List[KnowledgeBase]:
    return db.query(KnowledgeBase).offset(skip).limit(limit).all()

def update_knowledge_base(db: Session, knowledge_base_id: int, knowledge_base: KnowledgeBaseUpdate) -> Optional[KnowledgeBase]:
    db_knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if db_knowledge_base:
        for key, value in knowledge_base.dict(exclude_unset=True).items():
            setattr(db_knowledge_base, key, value)
        db.commit()
        db.refresh(db_knowledge_base)
        return db_knowledge_base
    return None

def delete_knowledge_base(db: Session, knowledge_base_id: int) -> Optional[KnowledgeBase]:
    db_knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if db_knowledge_base:
        db.delete(db_knowledge_base)
        db.commit()
        return db_knowledge_base
    return None