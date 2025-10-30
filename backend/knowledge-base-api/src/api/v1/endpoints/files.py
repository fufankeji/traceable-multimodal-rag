from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from src.crud.files import create_file_record
from src.db.sql.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class FileResponse(BaseModel):
    filename: str
    id: str
    status: str

@router.post("/files/upload", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), db: Session = next(get_db())):
    try:
        # Store the file and create a record in the database
        file_record = await create_file_record(db=db, file=file)
        return FileResponse(filename=file.filename, id=file_record.id, status="uploaded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(file_id: str, db: Session = next(get_db())):
    try:
        file_record = await get_file_record(db=db, file_id=file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(filename=file_record.filename, id=file_record.id, status="found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))