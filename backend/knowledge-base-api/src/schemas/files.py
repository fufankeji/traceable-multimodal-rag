from pydantic import BaseModel
from typing import Optional

class FileCreate(BaseModel):
    filename: str
    database_name: str

class FileResponse(BaseModel):
    id: str
    filename: str
    status: str

class FileInfo(BaseModel):
    id: str
    filename: str
    database_name: str
    upload_status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None