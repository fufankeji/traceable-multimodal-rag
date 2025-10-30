from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from core.config import DATABASE_URL

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    file_count = Column(Integer)
    file_info = Column(Text)

class Chunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    text = Column(Text)
    filename = Column(String)
    unique_id = Column(String)

    document = relationship("Document", back_populates="chunks")

Document.chunks = relationship("Chunk", order_by=Chunk.id, back_populates="document")

class Metadata(Base):
    __tablename__ = 'metadata'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    key = Column(String)
    value = Column(String)

    document = relationship("Document", back_populates="metadata")

Document.metadata = relationship("Metadata", order_by=Metadata.id, back_populates="document")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)