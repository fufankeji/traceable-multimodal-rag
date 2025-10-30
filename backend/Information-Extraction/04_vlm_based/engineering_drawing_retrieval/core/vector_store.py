"""
向量数据库封装
支持Milvus/Qdrant/Chroma
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

from langchain_community.vectorstores import Milvus, Qdrant, Chroma
from langchain_core.documents import Document

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config
from .embedding_manager import EmbeddingManager


class EngineeringDrawingVectorStore:
    """
    工程图纸向量存储
    封装了向量数据库操作
    """

    def __init__(self, collection_name: Optional[str] = None):
        self.config = config.vector_store
        self.collection_name = collection_name or self.config.collection_name
        self.embedding_manager = EmbeddingManager()

        # 初始化向量数据库
        self.vector_store = None
        self._init_vector_store()

    def _init_vector_store(self):
        """初始化向量数据库"""
        db_type = self.config.db_type

        if db_type == "milvus":
            self._init_milvus()
        elif db_type == "qdrant":
            self._init_qdrant()
        elif db_type == "chroma":
            self._init_chroma()
        else:
            raise ValueError(f"不支持的向量数据库类型: {db_type}")

    def _init_milvus(self):
        """初始化Milvus"""
        try:
            from pymilvus import connections, utility

            # 连接Milvus
            connections.connect(
                alias="default",
                host=self.config.milvus_host,
                port=self.config.milvus_port
            )

            print(f"✓ 已连接到Milvus: {self.config.milvus_host}:{self.config.milvus_port}")

            # 检查集合是否存在
            if utility.has_collection(self.collection_name):
                print(f"✓ 集合已存在: {self.collection_name}")
            else:
                print(f"⚠ 集合不存在，将在首次添加数据时创建: {self.collection_name}")

            # 初始化LangChain的Milvus
            self.vector_store = Milvus(
                embedding_function=self.embedding_manager.text_embeddings,
                collection_name=self.collection_name,
                connection_args={
                    "host": self.config.milvus_host,
                    "port": self.config.milvus_port
                }
            )

        except Exception as e:
            print(f"⚠ Milvus初始化失败: {e}")
            print("确保Milvus服务已启动: docker-compose up -d")
            raise

    def _init_qdrant(self):
        """初始化Qdrant"""
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port
            )

            self.vector_store = Qdrant(
                client=client,
                collection_name=self.collection_name,
                embeddings=self.embedding_manager.text_embeddings
            )

            print(f"✓ 已连接到Qdrant: {self.config.qdrant_host}:{self.config.qdrant_port}")

        except Exception as e:
            print(f"⚠ Qdrant初始化失败: {e}")
            raise

    def _init_chroma(self):
        """初始化Chroma"""
        try:
            persist_directory = str(Path(config.cache_dir) / "chroma")
            Path(persist_directory).mkdir(parents=True, exist_ok=True)

            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_manager.text_embeddings,
                persist_directory=persist_directory
            )

            print(f"✓ Chroma已初始化: {persist_directory}")

        except Exception as e:
            print(f"⚠ Chroma初始化失败: {e}")
            raise

    async def add_drawing(
        self,
        image_path: str,
        description: str,
        metadata: Dict,
        image_vector: Optional[List[float]] = None
    ) -> str:
        """
        添加工程图纸到向量库

        Args:
            image_path: 图像路径
            description: VLM生成的描述
            metadata: 元数据（包含structured_data等）
            image_vector: 图像向量（可选）

        Returns:
            文档ID
        """
        # 准备元数据
        full_metadata = {
            "image_path": str(image_path),
            "image_type": metadata.get("image_type", "unknown"),
            "source": str(Path(image_path).name),
            **metadata
        }

        # 如果有图像向量，保存到元数据
        if image_vector:
            full_metadata["image_vector"] = json.dumps(image_vector)

        # 创建Document
        doc = Document(
            page_content=description,  # 使用VLM描述作为文本内容
            metadata=full_metadata
        )

        # 添加到向量库
        ids = self.vector_store.add_documents([doc])

        return ids[0] if ids else ""

    async def add_drawings_batch(
        self,
        drawings: List[Dict]
    ) -> List[str]:
        """
        批量添加工程图纸

        Args:
            drawings: 图纸列表，每个元素包含 {image_path, description, metadata}

        Returns:
            文档ID列表
        """
        documents = []

        for drawing in drawings:
            metadata = {
                "image_path": drawing["image_path"],
                "image_type": drawing.get("image_type", "unknown"),
                "source": Path(drawing["image_path"]).name,
                **drawing.get("metadata", {})
            }

            if "image_vector" in drawing:
                metadata["image_vector"] = json.dumps(drawing["image_vector"])

            doc = Document(
                page_content=drawing["description"],
                metadata=metadata
            )
            documents.append(doc)

        # 批量添加
        ids = self.vector_store.add_documents(documents)

        return ids

    async def search_by_text(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        基于文本查询

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            (Document, score)列表
        """
        # LangChain的similarity_search_with_score
        results = self.vector_store.similarity_search_with_score(
            query,
            k=top_k,
            filter=filter_dict
        )

        return results

    async def search_by_image(
        self,
        image_path: str,
        top_k: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        基于图像查询（使用CLIP向量）

        Args:
            image_path: 查询图像路径
            top_k: 返回结果数量

        Returns:
            (Document, score)列表
        """
        # 获取查询图像的向量
        query_vector = await self.embedding_manager.embed_image(image_path)

        # TODO: 实现基于图像向量的检索
        # 目前LangChain的Milvus不直接支持，需要使用原生pymilvus API
        raise NotImplementedError("图像检索功能待实现")

    async def hybrid_search(
        self,
        text_query: Optional[str] = None,
        image_query: Optional[str] = None,
        top_k: int = 10,
        text_weight: float = 0.6,
        image_weight: float = 0.4
    ) -> List[Tuple[Document, float]]:
        """
        混合检索（文本 + 图像）

        Args:
            text_query: 文本查询
            image_query: 图像路径
            top_k: 返回结果数量
            text_weight: 文本权重
            image_weight: 图像权重

        Returns:
            (Document, score)列表
        """
        results = {}

        # 文本检索
        if text_query:
            text_results = await self.search_by_text(text_query, top_k=top_k * 2)
            for doc, score in text_results:
                doc_id = doc.metadata.get("image_path", "")
                if doc_id not in results:
                    results[doc_id] = {"doc": doc, "text_score": 0, "image_score": 0}
                results[doc_id]["text_score"] = score

        # 图像检索（如果实现）
        if image_query:
            # image_results = await self.search_by_image(image_query, top_k=top_k * 2)
            # 合并结果...
            pass

        # 计算混合分数
        final_results = []
        for doc_id, data in results.items():
            hybrid_score = (
                data["text_score"] * text_weight +
                data["image_score"] * image_weight
            )
            final_results.append((data["doc"], hybrid_score))

        # 排序并返回top_k
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results[:top_k]

    def delete_by_filter(self, filter_dict: Dict):
        """根据过滤条件删除文档"""
        # TODO: 实现删除功能
        raise NotImplementedError("删除功能待实现")

    def get_collection_stats(self) -> Dict:
        """获取集合统计信息"""
        if self.config.db_type == "milvus":
            from pymilvus import Collection
            collection = Collection(self.collection_name)
            return {
                "num_entities": collection.num_entities,
                "collection_name": self.collection_name
            }
        else:
            return {"message": "统计信息暂不支持该数据库"}


# 便捷函数
async def quick_add_drawing(
    image_path: str,
    description: str,
    metadata: Dict
) -> str:
    """快速添加图纸"""
    store = EngineeringDrawingVectorStore()
    return await store.add_drawing(image_path, description, metadata)


async def quick_search(query: str, top_k: int = 10) -> List[Tuple[Document, float]]:
    """快速搜索"""
    store = EngineeringDrawingVectorStore()
    return await store.search_by_text(query, top_k)


if __name__ == "__main__":
    import asyncio

    async def test():
        store = EngineeringDrawingVectorStore()

        # 测试添加
        # doc_id = await store.add_drawing(
        #     image_path="/path/to/drawing.png",
        #     description="这是一个测试图纸",
        #     metadata={"image_type": "engineering_drawing"}
        # )
        # print(f"添加文档ID: {doc_id}")

        # 测试搜索
        results = await store.search_by_text("测试查询", top_k=5)
        print(f"搜索结果: {len(results)} 条")

        # 统计信息
        stats = store.get_collection_stats()
        print(f"集合统计: {stats}")

    asyncio.run(test())
