from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============ 上传相关 ============

class ChunkData(BaseModel):
    """Chunk数据模型"""
    page_start: int
    page_end: int
    pages: List[int]
    text: str
    text_length: int
    continued: bool
    cross_page_bridge: bool
    is_table_like: bool

class UploadRequest(BaseModel):
    """上传文件请求"""
    knowledge_base_name: str = Field(..., description="知识库名称")
    filename: str = Field(..., description="文件名")
    file_id: Optional[str] = Field(None, description="文件唯一ID，如果不提供则自动生成")
    chunks: List[ChunkData] = Field(..., description="文本块列表")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="文件元数据")

class UploadResponse(BaseModel):
    """上传文件响应"""
    success: bool
    message: str
    filename: str
    file_id: str
    knowledge_base_name: str
    chunk_count: int

# ============ 检索相关 ============

class SearchRequest(BaseModel):
    """检索请求"""
    knowledge_base_name: str = Field(..., description="知识库名称")
    query: str = Field(..., description="检索查询文本")
    top_k: Optional[int] = Field(5, description="返回结果数量")
    similarity_threshold: Optional[float] = Field(0.0, description="相似度阈值")

class SearchResult(BaseModel):
    """单条检索结果"""
    chunk_id: str
    chunk_text: str
    filename: str
    file_id: str
    page_start: int
    page_end: int
    similarity_score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    """检索响应"""
    success: bool
    query: str
    results: List[SearchResult]
    count: int

# ============ 删除相关 ============

class DeleteFileRequest(BaseModel):
    """删除文件请求"""
    file_id: str = Field(..., description="文件唯一ID")
    knowledge_base_name: str = Field(..., description="知识库名称")

class DeleteFileResponse(BaseModel):
    """删除文件响应"""
    success: bool
    message: str
    file_id: str
    deleted_chunks: int

class DeleteKnowledgeBaseRequest(BaseModel):
    """删除知识库请求"""
    knowledge_base_name: str = Field(..., description="知识库名称")

class DeleteKnowledgeBaseResponse(BaseModel):
    """删除知识库响应"""
    success: bool
    message: str
    knowledge_base_name: str
    deleted_files: int
    deleted_chunks: int

# ============ 查询相关 ============

class FileInfo(BaseModel):
    """文件信息"""
    file_id: str
    filename: str
    chunk_count: int
    created_at: datetime
    metadata: Dict[str, Any]

class KnowledgeBaseInfo(BaseModel):
    """知识库信息"""
    name: str
    file_count: int
    created_at: datetime
    files: Optional[List[FileInfo]] = None

class ListKnowledgeBasesResponse(BaseModel):
    """知识库列表响应"""
    success: bool
    knowledge_bases: List[KnowledgeBaseInfo]
    total: int

class ListFilesResponse(BaseModel):
    """文件列表响应"""
    success: bool
    knowledge_base_name: str
    files: List[FileInfo]
    total: int