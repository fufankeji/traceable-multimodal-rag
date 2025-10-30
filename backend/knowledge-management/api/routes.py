from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.sql_db import get_db, SQLDBManager
from services.storage_service import StorageService
from services.retrieval_service import RetrievalService
from models.schemas import (
    UploadRequest, UploadResponse,
    SearchRequest, SearchResponse, SearchResult,
    DeleteFileRequest, DeleteFileResponse,
    DeleteKnowledgeBaseRequest, DeleteKnowledgeBaseResponse,
    ListKnowledgeBasesResponse, ListFilesResponse,
    KnowledgeBaseInfo, FileInfo
)
from typing import List

router = APIRouter()

# ============ 上传相关 ============

@router.post("/upload", response_model=UploadResponse)
async def upload_file(request: UploadRequest, db: Session = Depends(get_db)):
    """
    上传文件到知识库
    
    - **knowledge_base_name**: 知识库名称
    - **filename**: 文件名
    - **file_id**: 文件唯一ID（可选，不提供则自动生成）
    - **chunks**: chunk列表
    - **metadata**: 文件元数据（可选）
    """
    try:
        sql_manager = SQLDBManager(db)
        storage_service = StorageService(sql_manager)
        
        result = await storage_service.upload_file(
            knowledge_base_name=request.knowledge_base_name,
            filename=request.filename,
            chunks=request.chunks,
            file_id=request.file_id,
            file_metadata=request.metadata
        )
        
        return UploadResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ 检索相关 ============

@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest, db: Session = Depends(get_db)):
    """
    在知识库中检索
    
    - **knowledge_base_name**: 知识库名称
    - **query**: 查询文本
    - **top_k**: 返回结果数量（默认5）
    - **similarity_threshold**: 相似度阈值（默认0.0）
    """
    try:
        sql_manager = SQLDBManager(db)
        retrieval_service = RetrievalService(sql_manager)
        
        results = await retrieval_service.search(
            knowledge_base_name=request.knowledge_base_name,
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        search_results = [SearchResult(**result) for result in results]
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=search_results,
            count=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunk/{chunk_id}/context")
async def get_chunk_context(
    chunk_id: str,
    before: int = 1,
    after: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取chunk的上下文
    
    - **chunk_id**: chunk ID
    - **before**: 前面的chunk数量（默认1）
    - **after**: 后面的chunk数量（默认1）
    """
    try:
        sql_manager = SQLDBManager(db)
        retrieval_service = RetrievalService(sql_manager)
        
        context = retrieval_service.get_chunk_context(chunk_id, before, after)
        
        return {
            "success": True,
            "chunk_id": chunk_id,
            "context": context
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ 删除相关 ============

@router.delete("/file", response_model=DeleteFileResponse)
async def delete_file(request: DeleteFileRequest, db: Session = Depends(get_db)):
    """
    删除文件
    
    - **file_id**: 文件唯一ID
    - **knowledge_base_name**: 知识库名称
    """
    try:
        sql_manager = SQLDBManager(db)
        storage_service = StorageService(sql_manager)
        
        result = storage_service.delete_file(
            file_id=request.file_id,
            knowledge_base_name=request.knowledge_base_name
        )
        
        return DeleteFileResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge-base", response_model=DeleteKnowledgeBaseResponse)
async def delete_knowledge_base(request: DeleteKnowledgeBaseRequest, db: Session = Depends(get_db)):
    """
    删除知识库
    
    - **knowledge_base_name**: 知识库名称
    """
    try:
        sql_manager = SQLDBManager(db)
        storage_service = StorageService(sql_manager)
        
        result = storage_service.delete_knowledge_base(
            knowledge_base_name=request.knowledge_base_name
        )
        
        return DeleteKnowledgeBaseResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ 查询相关 ============

@router.get("/knowledge-bases", response_model=ListKnowledgeBasesResponse)
async def list_knowledge_bases(db: Session = Depends(get_db)):
    """
    列出所有知识库
    """
    try:
        sql_manager = SQLDBManager(db)
        storage_service = StorageService(sql_manager)
        
        knowledge_bases = storage_service.list_knowledge_bases()
        
        kb_infos = [KnowledgeBaseInfo(**kb) for kb in knowledge_bases]
        
        return ListKnowledgeBasesResponse(
            success=True,
            knowledge_bases=kb_infos,
            total=len(kb_infos)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/{knowledge_base_name}/files", response_model=ListFilesResponse)
async def list_files(knowledge_base_name: str, db: Session = Depends(get_db)):
    """
    列出知识库下的所有文件
    
    - **knowledge_base_name**: 知识库名称
    """
    try:
        sql_manager = SQLDBManager(db)
        storage_service = StorageService(sql_manager)
        
        files = storage_service.list_files(knowledge_base_name)
        
        file_infos = [FileInfo(**file) for file in files]
        
        return ListFilesResponse(
            success=True,
            knowledge_base_name=knowledge_base_name,
            files=file_infos,
            total=len(file_infos)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{file_id}")
async def get_file_info(file_id: str, db: Session = Depends(get_db)):
    """
    获取文件信息
    
    - **file_id**: 文件唯一ID
    """
    try:
        sql_manager = SQLDBManager(db)
        storage_service = StorageService(sql_manager)
        
        file_info = storage_service.get_file_info(file_id)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "success": True,
            "file": file_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))