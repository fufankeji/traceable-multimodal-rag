from sqlalchemy.orm import Session
from models.milvus.collection import VectorCollection
from core.milvus_client import milvus_client
from models.schemas.vector import VectorCreate, VectorResponse

class VectorService:
    def __init__(self, db: Session):
        self.db = db

    def upload_vector(self, vector_data: VectorCreate) -> VectorResponse:
        # Insert vector into Milvus
        vector_id = milvus_client.insert_vector(vector_data.vector)
        
        # Save vector metadata to SQL database
        new_vector = VectorCollection(
            id=vector_id,
            filename=vector_data.filename,
            vector=vector_data.vector,
            metadata=vector_data.metadata
        )
        self.db.add(new_vector)
        self.db.commit()
        self.db.refresh(new_vector)
        
        return VectorResponse(id=new_vector.id, status="success")

    def query_vector(self, vector_id: str) -> VectorCollection:
        # Query vector from SQL database
        vector = self.db.query(VectorCollection).filter(VectorCollection.id == vector_id).first()
        return vector

    def delete_vector(self, vector_id: str) -> str:
        # Delete vector from Milvus
        milvus_client.delete_vector(vector_id)
        
        # Delete vector metadata from SQL database
        self.db.query(VectorCollection).filter(VectorCollection.id == vector_id).delete()
        self.db.commit()
        
        return "Vector deleted successfully"