from sqlalchemy.orm import Session
from models.database.document import Document
from models.database.chunk import Chunk
from models.schemas.document import DocumentCreate, DocumentResponse
from core.database import get_db

class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def upload_document(self, document_data: DocumentCreate) -> DocumentResponse:
        new_document = Document(**document_data.dict())
        self.db.add(new_document)
        self.db.commit()
        self.db.refresh(new_document)
        return DocumentResponse.from_orm(new_document)

    def find_document(self, document_id: int) -> DocumentResponse:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if document:
            return DocumentResponse.from_orm(document)
        return None

    def delete_document(self, document_id: int) -> bool:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False

    def list_documents(self):
        return self.db.query(Document).all()