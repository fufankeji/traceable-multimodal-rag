from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.milvus_client import get_milvus_client

def get_database_session(db: Session = Depends(get_db)):
    return db

def get_milvus_connection(milvus_client = Depends(get_milvus_client)):
    return milvus_client