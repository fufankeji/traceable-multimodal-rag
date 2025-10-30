from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MILVUS_HOST: str
    MILVUS_PORT: int
    MILVUS_COLLECTION_NAME: str

    class Config:
        env_file = ".env"

settings = Settings()