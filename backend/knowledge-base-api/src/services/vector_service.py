from sqlalchemy.orm import Session
from db.milvus.client import MilvusClient
from schemas.responses import UploadResponse
from utils.embedding import generate_embedding

class VectorService:
    def __init__(self, db: Session, milvus_client: MilvusClient):
        self.db = db
        self.milvus_client = milvus_client

    def store_vector(self, file_id: str, vector: list, metadata: dict) -> UploadResponse:
        # Store the vector in Milvus
        self.milvus_client.insert_vector(file_id, vector, metadata)
        
        return UploadResponse(
            filename=file_id,
            unique_id=file_id,
            upload_status="success"
        )

    def search_vectors(self, query_vector: list, top_k: int):
        # Search for similar vectors in Milvus
        results = self.milvus_client.search(query_vector, top_k)
        return results

    def delete_vector(self, file_id: str):
        # Delete the vector from Milvus
        self.milvus_client.delete_vector(file_id)