from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Chunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    chunk_text = Column(String, nullable=False)
    unique_id = Column(String, unique=True, index=True)
    additional_info = Column(String)  # Optional field for any extra information

    def __repr__(self):
        return f"<Chunk(id={self.id}, filename={self.filename}, unique_id={self.unique_id})>"