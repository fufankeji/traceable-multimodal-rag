from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    file_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    files = relationship("File", back_populates="knowledge_base", cascade="all, delete-orphan")

class File(Base):
    """文件表"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), unique=True, nullable=False, index=True)  # UUID
    filename = Column(String(512), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    chunk_count = Column(Integer, default=0)
    metadata = Column(JSON, default={})  # 存储额外信息
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="files")
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")

class Chunk(Base):
    """文本块表"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), unique=True, nullable=False, index=True)  # UUID
    file_id = Column(String(255), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    page_start = Column(Integer)
    page_end = Column(Integer)
    text_length = Column(Integer)
    metadata = Column(JSON, default={})  # 存储其他信息（continued, cross_page_bridge等）
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    file = relationship("File", back_populates="chunks")