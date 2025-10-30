"""
向量化管理器
支持文本和图像的向量化
"""
import asyncio
from typing import List, Union
from pathlib import Path
import numpy as np

from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config


class EmbeddingManager:
    """
    向量化管理器
    支持文本embedding和图像embedding
    """

    def __init__(self):
        self.config = config.embedding

        # 初始化文本embedding模型
        self.text_embeddings = OpenAIEmbeddings(
            model=self.config.text_model,
            api_key=self.config.text_api_key,
            base_url=self.config.text_base_url
        )

        # 图像embedding（CLIP）
        self.image_embeddings = None
        if self.config.use_local_clip:
            self._init_clip()

    def _init_clip(self):
        """初始化本地CLIP模型"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            from PIL import Image

            self.clip_model = CLIPModel.from_pretrained(self.config.image_model)
            self.clip_processor = CLIPProcessor.from_pretrained(self.config.image_model)
            self.clip_device = "cuda" if torch.cuda.is_available() else "cpu"
            self.clip_model.to(self.clip_device)
            print(f"✓ CLIP模型加载成功 (device: {self.clip_device})")

        except ImportError:
            print("⚠ transformers未安装，图像embedding将被禁用")
            print("安装命令: pip install transformers torch")

    async def embed_text(self, text: str) -> List[float]:
        """
        文本向量化

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        try:
            # LangChain的embed_query是同步的，包装为异步
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.text_embeddings.embed_query,
                text
            )
            return embedding

        except Exception as e:
            print(f"文本向量化失败: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.text_embeddings.embed_documents,
                texts
            )
            return embeddings

        except Exception as e:
            print(f"批量文本向量化失败: {e}")
            raise

    async def embed_image(self, image_path: str) -> List[float]:
        """
        图像向量化（使用CLIP）

        Args:
            image_path: 图像路径

        Returns:
            图像向量
        """
        if not self.config.use_local_clip or self.clip_model is None:
            raise RuntimeError("CLIP模型未初始化，请设置 use_local_clip=True")

        try:
            from PIL import Image
            import torch

            # 加载图像
            image = Image.open(image_path).convert("RGB")

            # 预处理
            inputs = self.clip_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.clip_device) for k, v in inputs.items()}

            # 获取图像特征
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)

            # 归一化
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # 转为列表
            embedding = image_features.cpu().numpy().flatten().tolist()

            return embedding

        except Exception as e:
            print(f"图像向量化失败: {e}")
            raise

    async def embed_images(self, image_paths: List[str]) -> List[List[float]]:
        """
        批量图像向量化

        Args:
            image_paths: 图像路径列表

        Returns:
            图像向量列表
        """
        embeddings = []
        for path in image_paths:
            try:
                embedding = await self.embed_image(path)
                embeddings.append(embedding)
            except Exception as e:
                print(f"图像向量化失败 {path}: {e}")
                embeddings.append([])

        return embeddings

    def cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """
        计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度分数 [0, 1]
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # 归一化到 [0, 1]
        return float((similarity + 1) / 2)


# 便捷函数
async def quick_embed_text(text: str) -> List[float]:
    """快速文本向量化"""
    manager = EmbeddingManager()
    return await manager.embed_text(text)


async def quick_embed_image(image_path: str) -> List[float]:
    """快速图像向量化"""
    manager = EmbeddingManager()
    return await manager.embed_image(image_path)


if __name__ == "__main__":
    # 测试代码
    async def test():
        manager = EmbeddingManager()

        # 测试文本embedding
        text_vec = await manager.embed_text("这是一个测试文本")
        print(f"文本向量维度: {len(text_vec)}")
        print(f"前10个值: {text_vec[:10]}")

        # 测试批量
        texts = ["文本1", "文本2", "文本3"]
        text_vecs = await manager.embed_texts(texts)
        print(f"批量文本向量: {len(text_vecs)} 条")

    asyncio.run(test())
