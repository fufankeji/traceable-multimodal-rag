import httpx
from typing import List
from config import settings
import uuid

async def generate_embedding(text: str) -> List[float]:
    """
    调用在线embedding API生成向量
    
    Args:
        text: 输入文本
    
    Returns:
        向量列表
    """
    if not settings.EMBEDDING_API_KEY:
        raise ValueError("未配置EMBEDDING_API_KEY，请在配置文件或环境变量中设置")
    
    headers = {
        "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.EMBEDDING_MODEL,
        "input": text
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result["data"][0]["embedding"]
            return embedding
            
        except httpx.HTTPError as e:
            raise Exception(f"Embedding API调用失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Embedding API响应格式错误: {str(e)}")

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    批量生成embedding
    
    Args:
        texts: 文本列表
    
    Returns:
        向量列表
    """
    if not settings.EMBEDDING_API_KEY:
        raise ValueError("未配置EMBEDDING_API_KEY，请在配置文件或环境变量中设置")
    
    headers = {
        "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.EMBEDDING_MODEL,
        "input": texts
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            return embeddings
            
        except httpx.HTTPError as e:
            raise Exception(f"Embedding API调用失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Embedding API响应格式错误: {str(e)}")

def generate_file_id() -> str:
    """生成文件唯一ID"""
    return str(uuid.uuid4())

def generate_chunk_id() -> str:
    """生成chunk唯一ID"""
    return str(uuid.uuid4())

def validate_knowledge_base_name(name: str) -> bool:
    """验证知识库名称是否合法"""
    if not name or len(name) < 1 or len(name) > 255:
        return False
    # 可以添加更多验证规则
    return True