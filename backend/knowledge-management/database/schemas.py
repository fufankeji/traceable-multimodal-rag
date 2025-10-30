from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.sql_models import Base, KnowledgeBase, File, Chunk
from config import settings
from typing import Optional, List
import uuid

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_pre_ping=True
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SQLDBManager:
    """SQL数据库管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ 知识库操作 ============
    
    def create_knowledge_base(self, name: str) -> KnowledgeBase:
        """创建知识库"""
        kb = self.get_knowledge_base(name)
        if kb:
            return kb
        
        kb = KnowledgeBase(name=name, file_count=0)
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb
    
    def get_knowledge_base(self, name: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()
    
    def list_knowledge_bases(self) -> List[KnowledgeBase]:
        """列出所有知识库"""
        return self.db.query(KnowledgeBase).all()
    
    def delete_knowledge_base(self, name: str) -> bool:
        """删除知识库"""
        kb = self.get_knowledge_base(name)
        if not kb:
            return False
        
        self.db.delete(kb)
        self.db.commit()
        return True
    
    def update_knowledge_base_file_count(self, name: str):
        """更新知识库文件数量"""
        kb = self.get_knowledge_base(name)
        if kb:
            kb.file_count = self.db.query(File).filter(File.knowledge_base_id == kb.id).count()
            self.db.commit()
    
    # ============ 文件操作 ============
    
    def create_file(self, file_id: str, filename: str, knowledge_base_name: str, metadata: dict = None) -> File:
        """创建文件记录"""
        kb = self.create_knowledge_base(knowledge_base_name)
        
        file = File(
            file_id=file_id,
            filename=filename,
            knowledge_base_id=kb.id,
            chunk_count=0,
            metadata=metadata or {}
        )
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        
        # 更新知识库文件数量
        self.update_knowledge_base_file_count(knowledge_base_name)
        return file
    
    def get_file_by_id(self, file_id: str) -> Optional[File]:
        """根据file_id获取文件"""
        return self.db.query(File).filter(File.file_id == file_id).first()
    
    def get_files_by_knowledge_base(self, knowledge_base_name: str) -> List[File]:
        """获取知识库下的所有文件"""
        kb = self.get_knowledge_base(knowledge_base_name)
        if not kb:
            return []
        return self.db.query(File).filter(File.knowledge_base_id == kb.id).all()
    
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        file = self.get_file_by_id(file_id)
        if not file:
            return False
        
        kb_id = file.knowledge_base_id
        self.db.delete(file)
        self.db.commit()
        
        # 更新知识库文件数量
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb:
            self.update_knowledge_base_file_count(kb.name)
        
        return True
    
    def update_file_chunk_count(self, file_id: str):
        """更新文件的chunk数量"""
        file = self.get_file_by_id(file_id)
        if file:
            file.chunk_count = self.db.query(Chunk).filter(Chunk.file_id == file_id).count()
            self.db.commit()
    
    # ============ Chunk操作 ============
    
    def create_chunk(self, file_id: str, text: str, page_start: int, page_end: int, 
                    text_length: int, metadata: dict = None) -> Chunk:
        """创建chunk记录"""
        chunk_id = str(uuid.uuid4())
        
        chunk = Chunk(
            chunk_id=chunk_id,
            file_id=file_id,
            text=text,
            page_start=page_start,
            page_end=page_end,
            text_length=text_length,
            metadata=metadata or {}
        )
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        
        # 更新文件的chunk数量
        self.update_file_chunk_count(file_id)
        return chunk
    
    def get_chunks_by_file(self, file_id: str) -> List[Chunk]:
        """获取文件的所有chunks"""
        return self.db.query(Chunk).filter(Chunk.file_id == file_id).all()
    
    def delete_chunks_by_file(self, file_id: str) -> int:
        """删除文件的所有chunks"""
        count = self.db.query(Chunk).filter(Chunk.file_id == file_id).count()
        self.db.query(Chunk).filter(Chunk.file_id == file_id).delete()
        self.db.commit()
        return count
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """根据chunk_id获取chunk"""
        return self.db.query(Chunk).filter(Chunk.chunk_id == chunk_id).first()