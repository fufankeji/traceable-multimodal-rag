"""
混合检索器
结合文本检索、图像检索、重排序等功能
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import asyncio

from langchain_core.documents import Document

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config
from core.vector_store import EngineeringDrawingVectorStore
from core.embedding_manager import EmbeddingManager


class SearchResult:
    """检索结果"""
    def __init__(
        self,
        image_path: str,
        description: str,
        score: float,
        metadata: Dict,
        rank: int = 0
    ):
        self.image_path = image_path
        self.description = description
        self.score = score
        self.metadata = metadata
        self.rank = rank

    def to_dict(self) -> Dict:
        return {
            "rank": self.rank,
            "image_path": self.image_path,
            "description": self.description,
            "score": round(self.score, 4),
            "image_type": self.metadata.get("image_type", "unknown"),
            "metadata": self.metadata
        }

    def __repr__(self):
        return f"SearchResult(rank={self.rank}, score={self.score:.3f}, path={self.image_path})"


class HybridRetriever:
    """
    混合检索器
    支持文本检索、图像检索、过滤、重排序
    """

    def __init__(self, collection_name: Optional[str] = None):
        self.config = config.retrieval
        self.vector_store = EngineeringDrawingVectorStore(collection_name)
        self.embedding_manager = EmbeddingManager()

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        image_type: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> List[SearchResult]:
        """
        基于文本查询

        Args:
            query: 查询文本
            top_k: 返回结果数量
            image_type: 过滤图像类型
            min_score: 最小相似度分数

        Returns:
            SearchResult列表
        """
        top_k = top_k or self.config.top_k
        min_score = min_score or self.config.similarity_threshold

        # 构建过滤条件
        filter_dict = {}
        if image_type:
            filter_dict["image_type"] = image_type

        # 向量检索
        raw_results = await self.vector_store.search_by_text(
            query,
            top_k=top_k * 2,  # 多取一些，后续过滤和重排序
            filter_dict=filter_dict if filter_dict else None
        )

        # 转换为SearchResult
        results = []
        for rank, (doc, score) in enumerate(raw_results, 1):
            # 过滤低分结果
            if score < min_score:
                continue

            result = SearchResult(
                image_path=doc.metadata.get("image_path", ""),
                description=doc.page_content,
                score=score,
                metadata=doc.metadata,
                rank=rank
            )
            results.append(result)

        # 重排序（如果启用）
        if self.config.enable_rerank and len(results) > 0:
            results = await self._rerank(query, results)

        # 返回top_k
        return results[:top_k]

    async def search_by_example(
        self,
        image_path: str,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        基于示例图像查询

        Args:
            image_path: 示例图像路径
            top_k: 返回结果数量

        Returns:
            SearchResult列表
        """
        # TODO: 实现基于图像的检索
        raise NotImplementedError("图像检索功能待实现")

    async def search_hybrid(
        self,
        text_query: Optional[str] = None,
        image_query: Optional[str] = None,
        top_k: Optional[int] = None,
        text_weight: Optional[float] = None,
        image_weight: Optional[float] = None
    ) -> List[SearchResult]:
        """
        混合检索（文本 + 图像）

        Args:
            text_query: 文本查询
            image_query: 图像路径
            top_k: 返回结果数量
            text_weight: 文本权重
            image_weight: 图像权重

        Returns:
            SearchResult列表
        """
        top_k = top_k or self.config.top_k
        text_weight = text_weight or self.config.text_weight
        image_weight = image_weight or self.config.image_weight

        raw_results = await self.vector_store.hybrid_search(
            text_query=text_query,
            image_query=image_query,
            top_k=top_k,
            text_weight=text_weight,
            image_weight=image_weight
        )

        # 转换为SearchResult
        results = []
        for rank, (doc, score) in enumerate(raw_results, 1):
            result = SearchResult(
                image_path=doc.metadata.get("image_path", ""),
                description=doc.page_content,
                score=score,
                metadata=doc.metadata,
                rank=rank
            )
            results.append(result)

        return results

    async def _rerank(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        重排序

        使用cross-encoder模型对结果重新排序

        Args:
            query: 查询文本
            results: 初始检索结果

        Returns:
            重排序后的结果
        """
        # TODO: 实现重排序
        # 可以使用 BGE-reranker 或 Cohere rerank API

        # 暂时返回原始结果
        return results

    async def search_with_filters(
        self,
        query: str,
        filters: Dict,
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        带过滤条件的搜索

        Args:
            query: 查询文本
            filters: 过滤条件 {"image_type": "cad_drawing", ...}
            top_k: 返回结果数量

        Returns:
            SearchResult列表
        """
        return await self.search(
            query=query,
            top_k=top_k,
            image_type=filters.get("image_type")
        )

    def format_results(self, results: List[SearchResult]) -> str:
        """
        格式化输出结果

        Args:
            results: 检索结果

        Returns:
            格式化字符串
        """
        if not results:
            return "未找到相关结果"

        output = [f"共找到 {len(results)} 条结果:\n"]

        for result in results:
            output.append(f"\n【第 {result.rank} 名】 (相似度: {result.score:.3f})")
            output.append(f"图像路径: {result.image_path}")
            output.append(f"图像类型: {result.metadata.get('image_type', 'unknown')}")
            output.append(f"描述: {result.description[:200]}...")
            output.append("-" * 60)

        return "\n".join(output)


# 便捷函数
async def quick_search(query: str, top_k: int = 10) -> List[SearchResult]:
    """快速搜索"""
    retriever = HybridRetriever()
    return await retriever.search(query, top_k)


if __name__ == "__main__":
    async def test():
        retriever = HybridRetriever()

        # 测试搜索
        query = "查找轴承相关的工程图纸"
        results = await retriever.search(query, top_k=5)

        print(retriever.format_results(results))

    asyncio.run(test())
