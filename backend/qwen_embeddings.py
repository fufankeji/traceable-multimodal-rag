"""
通义千问 Embedding 封装
支持 LangChain 的 Embeddings 接口
"""
import os
from typing import List
import httpx
from openai import OpenAI
from langchain.embeddings.base import Embeddings


class QwenEmbeddings(Embeddings):
    """通义千问 text-embedding-v4 模型封装"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "text-embedding-v4",
        dimensions: int = 1024,
        encoding_format: str = "float"
    ):
        """
        初始化通义千问 Embedding

        Args:
            api_key: DashScope API Key（如果未提供，从环境变量 DASHSCOPE_API_KEY 读取）
            base_url: API 地址
            model: 模型名称（text-embedding-v4 或 text-embedding-v3）
            dimensions: 向量维度（仅 v3 和 v4 支持，v4 最大 1024）
            encoding_format: 编码格式
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("必须提供 api_key 或设置环境变量 DASHSCOPE_API_KEY")

        self.base_url = base_url
        self.model = model
        self.dimensions = dimensions
        self.encoding_format = encoding_format

        # 初始化 OpenAI 客户端
        # 创建自定义 HTTP 客户端，避免 proxies 参数问题
        http_client = httpx.Client(
            timeout=60.0,
            follow_redirects=True
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client
        )

        print(f"✓ 初始化通义千问 Embedding")
        print(f"  模型: {self.model}")
        print(f"  维度: {self.dimensions}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对多个文档进行向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        embeddings = []

        # 批量处理（通义千问支持批量，但为了稳定性我们也可以单个处理）
        for text in texts:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                    dimensions=self.dimensions,
                    encoding_format=self.encoding_format
                )
                embedding = response.data[0].embedding
                embeddings.append(embedding)

            except Exception as e:
                print(f"⚠️ 向量化失败: {e}")
                # 失败时返回零向量
                embeddings.append([0.0] * self.dimensions)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        对查询文本进行向量化

        Args:
            text: 查询文本

        Returns:
            向量
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
                encoding_format=self.encoding_format
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"⚠️ 查询向量化失败: {e}")
            # 失败时返回零向量
            return [0.0] * self.dimensions


# 测试代码
if __name__ == "__main__":
    # 测试 Qwen Embeddings
    embeddings = QwenEmbeddings()

    # 测试单个文本
    text = "衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买"
    vector = embeddings.embed_query(text)
    print(f"\n文本: {text}")
    print(f"向量维度: {len(vector)}")
    print(f"向量前10维: {vector[:10]}")

    # 测试批量文本
    texts = [
        "这是第一段文本",
        "这是第二段文本",
        "这是第三段文本"
    ]
    vectors = embeddings.embed_documents(texts)
    print(f"\n批量向量化:")
    print(f"  文本数量: {len(texts)}")
    print(f"  向量数量: {len(vectors)}")
    print(f"  每个向量维度: {len(vectors[0])}")
