from database.sql_db import SQLDBManager
from database.milvus_db import milvus_manager
from utils import generate_embedding
from typing import List, Dict, Any
from config import settings

class RetrievalService:
    """检索服务"""
    
    def __init__(self, sql_manager: SQLDBManager):
        self.sql_manager = sql_manager
        self.milvus_manager = milvus_manager
    
    async def search(
        self,
        knowledge_base_name: str,
        query: str,
        top_k: int = None,
        similarity_threshold: float = None,
        filter_file_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        向量检索
        
        Args:
            knowledge_base_name: 知识库名称
            query: 查询文本
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            filter_file_ids: 过滤的文件ID列表（可选）
        
        Returns:
            检索结果列表
        """
        # 使用默认值
        if top_k is None:
            top_k = settings.TOP_K
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        try:
            # 1. 检查知识库是否存在
            kb = self.sql_manager.get_knowledge_base(knowledge_base_name)
            if not kb:
                raise ValueError(f"知识库 '{knowledge_base_name}' 不存在")
            
            # 2. 检查collection是否存在
            if not self.milvus_manager.collection_exists(knowledge_base_name):
                raise ValueError(f"知识库 '{knowledge_base_name}' 的向量索引不存在")
            
            # 3. 生成查询向量
            query_vector = await generate_embedding(query)
            
            # 4. 构建过滤表达式
            filter_expr = None
            if filter_file_ids:
                file_id_list = "', '".join(filter_file_ids)
                filter_expr = f"file_id in ['{file_id_list}']"
            
            # 5. 执行向量检索
            search_results = self.milvus_manager.search_vectors(
                knowledge_base_name=knowledge_base_name,
                query_vector=query_vector,
                top_k=top_k,
                filter_expr=filter_expr
            )
            
            # 6. 过滤低于阈值的结果
            filtered_results = [
                result for result in search_results
                if result["similarity_score"] >= similarity_threshold
            ]
            
            # 7. 补充SQL中的详细信息
            enriched_results = []
            for result in filtered_results:
                chunk = self.sql_manager.get_chunk_by_id(result["chunk_id"])
                if chunk:
                    enriched_result = {
                        "chunk_id": result["chunk_id"],
                        "chunk_text": result["chunk_text"],
                        "filename": result["filename"],
                        "file_id": result["file_id"],
                        "page_start": chunk.page_start,
                        "page_end": chunk.page_end,
                        "similarity_score": result["similarity_score"],
                        "metadata": chunk.metadata
                    }
                    enriched_results.append(enriched_result)
            
            return enriched_results
            
        except Exception as e:
            raise Exception(f"检索失败: {str(e)}")
    
    def get_chunk_context(
        self,
        chunk_id: str,
        before: int = 1,
        after: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取chunk的上下文
        
        Args:
            chunk_id: chunk ID
            before: 前面的chunk数量
            after: 后面的chunk数量
        
        Returns:
            上下文chunk列表
        """
        try:
            # 1. 获取当前chunk
            current_chunk = self.sql_manager.get_chunk_by_id(chunk_id)
            if not current_chunk:
                return []
            
            # 2. 获取同文件的所有chunks
            all_chunks = self.sql_manager.get_chunks_by_file(current_chunk.file_id)
            
            # 3. 按照创建时间排序
            all_chunks.sort(key=lambda x: x.created_at)
            
            # 4. 找到当前chunk的索引
            current_index = next(
                (i for i, chunk in enumerate(all_chunks) if chunk.chunk_id == chunk_id),
                -1
            )
            
            if current_index == -1:
                return []
            
            # 5. 获取上下文
            start_index = max(0, current_index - before)
            end_index = min(len(all_chunks), current_index + after + 1)
            
            context_chunks = all_chunks[start_index:end_index]
            
            # 6. 格式化返回
            return [
                {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "is_current": chunk.chunk_id == chunk_id,
                    "metadata": chunk.metadata
                }
                for chunk in context_chunks
            ]
            
        except Exception as e:
            raise Exception(f"获取上下文失败: {str(e)}")