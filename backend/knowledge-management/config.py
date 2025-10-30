import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SQL数据库配置
    DATABASE_URL: str = "sqlite:///./rag_knowledge_base.db"
    # 如果使用MySQL或PostgreSQL，可以改为：
    # DATABASE_URL: str = "mysql+pymysql://user:password@localhost/rag_db"
    # DATABASE_URL: str = "postgresql://user:password@localhost/rag_db"
    
    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    
    # Embedding配置
    EMBEDDING_API_URL: str = "https://api.openai.com/v1/embeddings"
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536  # text-embedding-3-small的维度
    
    # 向量检索配置
    TOP_K: int = 5  # 默认返回前5个最相关的结果
    SIMILARITY_THRESHOLD: float = 0.7  # 相似度阈值
    
    # 其他配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"

settings = Settings()