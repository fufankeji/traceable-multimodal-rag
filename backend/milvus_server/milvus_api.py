import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import numpy as np


# Pydantic 模型定义
class DocumentChunk(BaseModel):
    chunk_text: str
    filename: str
    file_id: Optional[str] = None
    embedding: List[float]
    metadata: Dict[str, Any] = {}


class UploadRequest(BaseModel):
    collection_name: str
    documents: List[DocumentChunk]


class UploadResponse(BaseModel):
    filename: str
    file_id: str
    status: str
    message: str


class SearchRequest(BaseModel):
    collection_name: str
    query_embedding: List[float]
    top_k: int = 10
    filter_expr: Optional[str] = None


class DeleteRequest(BaseModel):
    collection_name: str
    filename: str


class MilvusRAGService:
    def __init__(self, host: str = "localhost", port: str = "19530"):
        self.host = host
        self.port = port
        self.connect_to_milvus()
    
    def connect_to_milvus(self):
        """连接到Milvus服务"""
        try:
            connections.connect("default", host=self.host, port=self.port)
            print("Successfully connected to Milvus")
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            raise
    
    def create_collection_schema(self, embedding_dim: int = 768) -> CollectionSchema:
        """创建Collection的Schema"""
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="RAG Knowledge Base Collection"
        )
        return schema
    
    def create_or_get_collection(self, collection_name: str, embedding_dim: int = 768) -> Collection:
        """创建或获取Collection"""
        if utility.has_collection(collection_name):
            collection = Collection(collection_name)
        else:
            schema = self.create_collection_schema(embedding_dim)
            collection = Collection(name=collection_name, schema=schema)
            
            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
        
        return collection
    
    def insert_documents(self, collection_name: str, documents: List[DocumentChunk]) -> List[str]:
        """插入文档到Collection"""
        try:
            if not documents:
                return []
            
            # 检测embedding维度
            embedding_dim = len(documents[0].embedding)
            collection = self.create_or_get_collection(collection_name, embedding_dim)
            
            # 准备数据
            chunk_texts = []
            filenames = []
            file_ids = []
            embeddings = []
            metadatas = []
            created_ats = []
            
            current_time = datetime.now().isoformat()
            
            for doc in documents:
                # 如果没有file_id，生成一个
                if not doc.file_id:
                    doc.file_id = str(uuid.uuid4())
                
                chunk_texts.append(doc.chunk_text)
                filenames.append(doc.filename)
                file_ids.append(doc.file_id)
                embeddings.append(doc.embedding)
                metadatas.append(json.dumps(doc.metadata, ensure_ascii=False))
                created_ats.append(current_time)
            
            # 插入数据
            entities = [
                chunk_texts,
                filenames, 
                file_ids,
                embeddings,
                metadatas,
                created_ats
            ]
            
            collection.insert(entities)
            collection.flush()
            
            return file_ids
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"插入文档失败: {str(e)}")
    
    def search_similar_documents(self, collection_name: str, query_embedding: List[float], 
                               top_k: int = 10, filter_expr: Optional[str] = None) -> List[Dict]:
        """搜索相似文档"""
        try:
            if not utility.has_collection(collection_name):
                raise HTTPException(status_code=404, detail=f"Collection {collection_name} 不存在")
            
            collection = Collection(collection_name)
            collection.load()
            
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            output_fields = ["chunk_text", "filename", "file_id", "metadata", "created_at"]
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields
            )
            
            # 格式化结果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        "id": hit.id,
                        "score": hit.score,
                        "chunk_text": hit.entity.get("chunk_text"),
                        "filename": hit.entity.get("filename"),
                        "file_id": hit.entity.get("file_id"),
                        "metadata": json.loads(hit.entity.get("metadata", "{}")),
                        "created_at": hit.entity.get("created_at")
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
    
    def delete_documents_by_filename(self, collection_name: str, filename: str) -> int:
        """根据文件名删除文档"""
        try:
            if not utility.has_collection(collection_name):
                raise HTTPException(status_code=404, detail=f"Collection {collection_name} 不存在")
            
            collection = Collection(collection_name)
            collection.load()
            
            # 构建删除表达式
            expr = f'filename == "{filename}"'
            
            # 执行删除
            collection.delete(expr)
            collection.flush()
            
            return 1  # Milvus不直接返回删除的记录数
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """获取Collection信息"""
        try:
            if not utility.has_collection(collection_name):
                return {"exists": False}
            
            collection = Collection(collection_name)
            collection.load()
            
            return {
                "exists": True,
                "num_entities": collection.num_entities,
                "schema": str(collection.schema)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取Collection信息失败: {str(e)}")


# FastAPI 应用
app = FastAPI(title="Milvus RAG Service", version="1.0.0")

# 初始化Milvus服务
milvus_service = MilvusRAGService()


@app.post("/upload", response_model=List[UploadResponse])
async def upload_documents(request: UploadRequest):
    """上传文档到知识库"""
    try:
        file_ids = milvus_service.insert_documents(request.collection_name, request.documents)
        
        responses = []
        for i, doc in enumerate(request.documents):
            response = UploadResponse(
                filename=doc.filename,
                file_id=file_ids[i] if i < len(file_ids) else doc.file_id or str(uuid.uuid4()),
                status="success",
                message="文档上传成功"
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_documents(request: SearchRequest):
    """搜索相似文档"""
    try:
        results = milvus_service.search_similar_documents(
            collection_name=request.collection_name,
            query_embedding=request.query_embedding,
            top_k=request.top_k,
            filter_expr=request.filter_expr
        )
        
        return {
            "status": "success",
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete")
async def delete_documents(request: DeleteRequest):
    """删除文档"""
    try:
        deleted_count = milvus_service.delete_documents_by_filename(
            collection_name=request.collection_name,
            filename=request.filename
        )
        
        return {
            "status": "success",
            "message": f"已删除文件 {request.filename}",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collection/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """获取Collection信息"""
    try:
        info = milvus_service.get_collection_info(collection_name)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "Milvus RAG Service"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)