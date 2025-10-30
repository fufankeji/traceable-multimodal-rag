from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    milvus_host: str
    milvus_port: int

    class Config:
        env_file = ".env"

settings = Settings()