from database.sql_db import SQLDBManager
from database.milvus_db import milvus_manager
from utils import generate_embeddings_batch, generate_file_id
from models.schemas import ChunkData
from typing import List, Dict, Any
import uuid

class StorageService:
    """数据存储服务"""
    
    def __init__(self, sql_manager: SQLDBManager):
        self.sql_manager = sql_manager
        self.milvus_manager = milvus_manager
    
    async def upload_file(
        self,
        knowledge_base_name: str,
        filename: str,
        chunks: List[ChunkData],
        file_id: str = None,
        file_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        上传文件到知识库
        
        Args:
            knowledge_base_name: 知识库名称
            filename: 文件名
            chunks: chunk列表
            file_id: 文件ID（可选，不提供则自动生成）
            file_metadata: 文件元数据
        
        Returns:
            上传结果
        """
        # 生成file_id（如果未提供）
        if not file_id:
            file_id = generate_file_id()
        
        try:
            # 1. 在SQL中创建知识库（如果不存在）
            self.sql_manager.create_knowledge_base(knowledge_base_name)
            
            # 2. 在Milvus中创建collection（如果不存在）
            self.milvus_manager.create_collection(knowledge_base_name)
            
            # 3. 在SQL中创建文件记录
            file_record = self.sql_manager.create_file(
                file_id=file_id,
                filename=filename,
                knowledge_base_name=knowledge_base_name,
                metadata=file_metadata or {}
            )
            
            # 4. 处理chunks
            chunk_texts = [chunk.text for chunk in chunks]
            
            # 5. 批量生成embeddings
            embeddings = await generate_embeddings_batch(chunk_texts)
            
            # 6. 准备SQL和Milvus的数据
            milvus_data = []
            
            for i, chunk in enumerate(chunks):
                # 生成chunk_id
                chunk_id = str(uuid.uuid4())
                
                # 准备chunk元数据
                chunk_metadata = {
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "pages": chunk.pages,
                    "text_length": chunk.text_length,
                    "continued": chunk.continued,
                    "cross_page_bridge": chunk.cross_page_bridge,
                    "is_table_like": chunk.is_table_like
                }
                
                # 在SQL中创建chunk记录
                self.sql_manager.create_chunk(
                    file_id=file_id,
                    text=chunk.text,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    text_length=chunk.text_length,
                    metadata=chunk_metadata
                )
                
                # 准备Milvus数据
                milvus_data.append({
                    "chunk_id": chunk_id,
                    "chunk_text": chunk.text,
                    "filename": filename,
                    "file_id": file_id,
                    "embedding": embeddings[i],
                    "metadata": chunk_metadata
                })
            
            # 7. 插入向量到Milvus
            self.milvus_manager.insert_vectors(knowledge_base_name, milvus_data)
            
            return {
                "success": True,
                "message": "文件上传成功",
                "filename": filename,
                "file_id": file_id,
                "knowledge_base_name": knowledge_base_name,
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            # 回滚：删除已创建的数据
            try:
                self.sql_manager.delete_file(file_id)
            except:
                pass
            
            raise Exception(f"文件上传失败: {str(e)}")
    
    def delete_file(self, file_id: str, knowledge_base_name: str) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            knowledge_base_name: 知识库名称
        
        Returns:
            删除结果
        """
        try:
            # 1. 获取文件信息
            file = self.sql_manager.get_file_by_id(file_id)
            if not file:
                return {
                    "success": False,
                    "message": "文件不存在",
                    "file_id": file_id,
                    "deleted_chunks": 0
                }
            
            # 2. 删除SQL中的chunks（会级联删除）
            deleted_chunks = self.sql_manager.delete_chunks_by_file(file_id)
            
            # 3. 删除Milvus中的向量
            if self.milvus_manager.collection_exists(knowledge_base_name):
                self.milvus_manager.delete_by_file_id(knowledge_base_name, file_id)
            
            # 4. 删除SQL中的文件记录
            self.sql_manager.delete_file(file_id)
            
            return {
                "success": True,
                "message": "文件删除成功",
                "file_id": file_id,
                "deleted_chunks": deleted_chunks
            }
            
        except Exception as e:
            raise Exception(f"文件删除失败: {str(e)}")
    
    def delete_knowledge_base(self, knowledge_base_name: str) -> Dict[str, Any]:
        """
        删除知识库
        
        Args:
            knowledge_base_name: 知识库名称
        
        Returns:
            删除结果
        """
        try:
            # 1. 获取知识库信息
            kb = self.sql_manager.get_knowledge_base(knowledge_base_name)
            if not kb:
                return {
                    "success": False,
                    "message": "知识库不存在",
                    "knowledge_base_name": knowledge_base_name,
                    "deleted_files": 0,
                    "deleted_chunks": 0
                }
            
            # 2. 统计文件和chunk数量
            files = self.sql_manager.get_files_by_knowledge_base(knowledge_base_name)
            deleted_files = len(files)
            deleted_chunks = sum(file.chunk_count for file in files)
            
            # 3. 删除Milvus中的collection
            if self.milvus_manager.collection_exists(knowledge_base_name):
                self.milvus_manager.delete_collection(knowledge_base_name)
            
            # 4. 删除SQL中的知识库（会级联删除文件和chunks）
            self.sql_manager.delete_knowledge_base(knowledge_base_name)
            
            return {
                "success": True,
                "message": "知识库删除成功",
                "knowledge_base_name": knowledge_base_name,
                "deleted_files": deleted_files,
                "deleted_chunks": deleted_chunks
            }
            
        except Exception as e:
            raise Exception(f"知识库删除失败: {str(e)}")
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
        
        Returns:
            文件信息
        """
        file = self.sql_manager.get_file_by_id(file_id)
        if not file:
            return None
        
        return {
            "file_id": file.file_id,
            "filename": file.filename,
            "chunk_count": file.chunk_count,
            "created_at": file.created_at,
            "metadata": file.metadata
        }
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        列出所有知识库
        
        Returns:
            知识库列表
        """
        kbs = self.sql_manager.list_knowledge_bases()
        return [
            {
                "name": kb.name,
                "file_count": kb.file_count,
                "created_at": kb.created_at
            }
            for kb in kbs
        ]
    
    def list_files(self, knowledge_base_name: str) -> List[Dict[str, Any]]:
        """
        列出知识库下的所有文件
        
        Args:
            knowledge_base_name: 知识库名称
        
        Returns:
            文件列表
        """
        files = self.sql_manager.get_files_by_knowledge_base(knowledge_base_name)
        return [
            {
                "file_id": file.file_id,
                "filename": file.filename,
                "chunk_count": file.chunk_count,
                "created_at": file.created_at,
                "metadata": file.metadata
            }
            for file in files
        ]