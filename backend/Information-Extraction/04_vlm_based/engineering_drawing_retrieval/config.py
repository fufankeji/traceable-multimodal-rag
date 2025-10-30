"""
配置文件
"""
from dataclasses import dataclass
from typing import Literal

@dataclass
class VLMConfig:
    """VLM模型配置"""
    # API配置
    api_key: str = "sk-Y4o8DF6Iq2l8OcieaS1gXfgIzFkfymV4oF01ofphYB5FxnFT"
    base_url: str = "https://aizex.top/v1"
    model_name: str = "gpt-4o"

    # 性能配置
    max_tokens: int = 2000
    temperature: float = 0.1  # 低温度保证稳定输出
    timeout: int = 60
    max_concurrent: int = 3  # 最大并发数

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ImageConfig:
    """图像处理配置"""
    # 图像质量
    max_size: int = 2000  # 最大尺寸
    jpeg_quality: int = 85

    # 预处理
    enable_denoise: bool = False  # 是否去噪
    enable_enhance: bool = True   # 是否增强
    enable_ocr: bool = True       # 是否启用OCR

    # OCR配置
    ocr_engine: Literal["paddleocr", "tesseract"] = "paddleocr"
    ocr_lang: str = "ch"  # ch=中英混合


@dataclass
class VectorStoreConfig:
    """向量数据库配置"""
    # 数据库类型
    db_type: Literal["milvus", "qdrant", "chroma"] = "milvus"

    # Milvus配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # Qdrant配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # 集合名称
    collection_name: str = "engineering_drawings"

    # 向量维度
    vector_dim: int = 1536  # text-embedding-3-small: 1536, large: 3072

    # 索引配置
    index_type: str = "IVF_FLAT"  # Milvus索引类型
    metric_type: str = "COSINE"   # 相似度度量


@dataclass
class EmbeddingConfig:
    """向量化配置"""
    # 文本Embedding
    text_model: str = "text-embedding-3-large"
    text_api_key: str = "sk-Y4o8DF6Iq2l8OcieaS1gXfgIzFkfymV4oF01ofphYB5FxnFT"
    text_base_url: str = "https://aizex.top/v1"

    # 图像Embedding (CLIP)
    image_model: str = "openai/clip-vit-large-patch14"
    use_local_clip: bool = False  # 是否使用本地CLIP

    # 批量处理
    batch_size: int = 10


@dataclass
class RetrievalConfig:
    """检索配置"""
    # 检索参数
    top_k: int = 10
    similarity_threshold: float = 0.7

    # 混合检索权重
    text_weight: float = 0.6
    image_weight: float = 0.4

    # 重排序
    enable_rerank: bool = True
    rerank_model: str = "bge-reranker-v2-m3"
    rerank_top_k: int = 5


@dataclass
class CacheConfig:
    """缓存配置"""
    enable_cache: bool = True
    cache_type: Literal["memory", "redis"] = "memory"

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # 缓存过期时间（秒）
    cache_ttl: int = 86400  # 24小时


@dataclass
class SystemConfig:
    """系统总配置"""
    vlm: VLMConfig = VLMConfig()
    image: ImageConfig = ImageConfig()
    vector_store: VectorStoreConfig = VectorStoreConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    cache: CacheConfig = CacheConfig()

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/system.log"

    # 输出目录
    output_dir: str = "output"
    cache_dir: str = "cache"


# 全局配置实例
config = SystemConfig()


# 图像类型定义
IMAGE_TYPES = {
    "engineering_drawing": "工程制造图纸",
    "cad_drawing": "CAD技术图纸",
    "floor_plan": "室内平面布置图/建筑平面图",
    "architecture_diagram": "系统架构图",
    "flowchart": "流程图",
    "technical_document": "技术文档图片",
    "circuit_diagram": "电路图",
    "mechanical_drawing": "机械设计图"
}
