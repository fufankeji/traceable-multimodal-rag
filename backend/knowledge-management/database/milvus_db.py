from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from config import settings
from typing import List, Dict, Any
import json

class MilvusDBManager:
    """Milvus数据库管理器"""
    
    def __init__(self):
        self.connect()
    
    def connect(self):
        """连接到Milvus"""
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD
            )
            print("✅ Milvus连接成功")
        except Exception as e:
            print(f"❌ Milvus连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开Milvus连接"""
        connections.disconnect("default")
    
    def _get_collection_name(self, knowledge_base_name: str) -> str:
        """生成collection名称"""
        # 确保collection名称符合Milvus规范（字母、数字、下划线）
        safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in knowledge_base_name)
        return f"kb_{safe_name}"
    
    def create_collection(self, knowledge_base_name: str) -> Collection:
        """创建collection"""
        collection_name = self._get_collection_name(knowledge_base_name)
        
        # 如果collection已存在，直接返回
        if utility.has_collection(collection_name):
            return Collection(collection_name)
        
        # 定义字段schema
        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=255),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)  # JSON字符串
        ]
        
        # 创建collection schema
        schema = CollectionSchema(
            fields=fields,
            description=f"Knowledge base: {knowledge_base_name}"
        )
        
        # 创建collection
        collection = Collection(
            name=collection_name,
            schema=schema
        )
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",  # 余弦相似度
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        print(f"✅ Collection '{collection_name}' 创建成功")
        return collection
    
    def get_collection(self, knowledge_base_name: str) -> Collection:
        """获取collection"""
        collection_name = self._get_collection_name(knowledge_base_name)
        
        if not utility.has_collection(collection_name):
            raise ValueError(f"Collection '{collection_name}' 不存在")
        
        return Collection(collection_name)
    
    def insert_vectors(self, knowledge_base_name: str, data: List[Dict[str, Any]]) -> List[str]:
        """插入向量数据
        
        Args:
            knowledge_base_name: 知识库名称
            data: 数据列表，每个元素包含：
                - chunk_id: chunk唯一ID
                - chunk_text: chunk文本
                - filename: 文件名
                - file_id: 文件ID
                - embedding: 向量
                - metadata: 元数据字典
        
        Returns:
            插入的chunk_id列表
        """
        collection = self.get_collection(knowledge_base_name)
        
        # 准备插入数据
        entities = [
            [item["chunk_id"] for item in data],
            [item["chunk_text"] for item in data],
            [item["filename"] for item in data],
            [item["file_id"] for item in data],
            [item["embedding"] for item in data],
            [json.dumps(item["metadata"], ensure_ascii=False) for item in data]
        ]
        
        # 插入数据
        collection.insert(entities)
        collection.flush()
        
        return [item["chunk_id"] for item in data]
    
    def search_vectors(self, knowledge_base_name: str, query_vector: List[float], 
                      top_k: int = 5, filter_expr: str = None) -> List[Dict[str, Any]]:
        """向量检索
        
        Args:
            knowledge_base_name: 知识库名称
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_expr: 过滤表达式（可选）
        
        Returns:
            检索结果列表
        """
        collection = self.get_collection(knowledge_base_name)
        collection.load()
        
        # 搜索参数
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # 执行搜索
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["chunk_id", "chunk_text", "filename", "file_id", "metadata"]
        )
        
        # 处理结果
        search_results = []
        for hits in results:
            for hit in hits:
                result = {
                    "chunk_id": hit.entity.get("chunk_id"),
                    "chunk_text": hit.entity.get("chunk_text"),
                    "filename": hit.entity.get("filename"),
                    "file_id": hit.entity.get("file_id"),
                    "similarity_score": float(hit.score),
                    "metadata": json.loads(hit.entity.get("metadata", "{}"))
                }
                search_results.append(result)
        
        return search_results
    
    def delete_by_file_id(self, knowledge_base_name: str, file_id: str) -> int:
        """根据file_id删除向量
        
        Args:
            knowledge_base_name: 知识库名称
            file_id: 文件ID
        
        Returns:
            删除的数量
        """
        collection = self.get_collection(knowledge_base_name)
        
        # 删除表达式
        expr = f'file_id == "{file_id}"'
        
        # 执行删除
        result = collection.delete(expr)
        collection.flush()
        
        return result.delete_count
    
    def delete_collection(self, knowledge_base_name: str) -> bool:
        """删除collection
        
        Args:
            knowledge_base_name: 知识库名称
        
        Returns:
            是否删除成功
        """
        collection_name = self._get_collection_name(knowledge_base_name)
        
        if not utility.has_collection(collection_name):
            return False
        
        utility.drop_collection(collection_name)
        print(f"✅ Collection '{collection_name}' 删除成功")
        return True
    
    def list_collections(self) -> List[str]:
        """列出所有collection"""
        return utility.list_collections()
    
    def collection_exists(self, knowledge_base_name: str) -> bool:
        """检查collection是否存在"""
        collection_name = self._get_collection_name(knowledge_base_name)
        return utility.has_collection(collection_name)

# 全局Milvus管理器实例
milvus_manager = MilvusDBManager()