from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Metadata(Base):
    __tablename__ = 'metadata'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    author = Column(String, index=True)
    created_at = Column(String)
    updated_at = Column(String)

    document = relationship("Document", back_populates="metadata")