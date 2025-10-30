from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    file_count = Column(Integer, default=0)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Document(id={self.id}, name={self.name}, file_count={self.file_count})>"