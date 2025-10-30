from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_bases'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    unique_id = Column(String(255), unique=True, nullable=False)
    upload_status = Column(String(50), nullable=False)

class Chunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)