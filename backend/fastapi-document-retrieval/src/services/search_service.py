from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.schemas.search import SearchRequest, SearchResponse
from core.database import get_db
from core.milvus_client import MilvusClient

class SearchService:
    def __init__(self, db: Session, milvus_client: MilvusClient):
        self.db = db
        self.milvus_client = milvus_client

    def search_documents(self, search_request: SearchRequest) -> SearchResponse:
        # Perform search in the SQL database
        documents = self.db.query(Document).filter(Document.title.contains(search_request.query)).all()
        
        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")

        # Perform vector search in Milvus
        vectors = [doc.vector for doc in documents]
        search_results = self.milvus_client.search(vectors)

        return SearchResponse(documents=documents, search_results=search_results)

def get_search_service(db: Session = Depends(get_db), milvus_client: MilvusClient = Depends(MilvusClient)):
    return SearchService(db=db, milvus_client=milvus_client)