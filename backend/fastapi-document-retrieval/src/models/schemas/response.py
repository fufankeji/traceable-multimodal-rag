from pydantic import BaseModel
from typing import Any, Dict

class ResponseModel(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] = {}  # Optional field for additional data

class ErrorResponseModel(BaseModel):
    status: str
    message: str
    error_code: int
    details: Dict[str, Any] = {}  # Optional field for error details