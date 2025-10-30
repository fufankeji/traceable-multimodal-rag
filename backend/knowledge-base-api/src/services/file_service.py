from fastapi import UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict
from ..db.sql import models
from ..crud import files as files_crud
from ..schemas.files import FileCreate, FileResponse
from ..core.database import get_db

class FileService:
    def __init__(self, db: Session):
        self.db = db

    def upload_file(self, file: UploadFile) -> FileResponse:
        file_data = FileCreate(filename=file.filename)
        db_file = files_crud.create_file(self.db, file_data)
        return FileResponse(id=db_file.id, filename=db_file.filename, status="uploaded")

    def delete_file(self, file_id: int) -> Dict[str, str]:
        files_crud.delete_file(self.db, file_id)
        return {"status": "deleted", "file_id": file_id}

    def get_file_info(self, file_id: int) -> FileResponse:
        db_file = files_crud.get_file(self.db, file_id)
        return FileResponse(id=db_file.id, filename=db_file.filename, status="found") if db_file else None

    def list_files(self) -> Dict[int, str]:
        return {file.id: file.filename for file in files_crud.get_all_files(self.db)}