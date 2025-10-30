from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from ..db.sql import models
from ..schemas.files import FileCreate, FileResponse

def create_file(db: Session, file: FileCreate) -> FileResponse:
    db_file = models.File(**file.dict())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return FileResponse(filename=db_file.filename, id=db_file.id, status="uploaded")

def get_file(db: Session, file_id: int) -> FileResponse:
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filename=db_file.filename, id=db_file.id, status="found")

def delete_file(db: Session, file_id: int) -> dict:
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(db_file)
    db.commit()
    return {"status": "deleted", "id": file_id}

def get_all_files(db: Session) -> List[FileResponse]:
    files = db.query(models.File).all()
    return [FileResponse(filename=file.filename, id=file.id, status="found") for file in files]