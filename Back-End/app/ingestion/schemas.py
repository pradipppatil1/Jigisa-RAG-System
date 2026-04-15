from pydantic import BaseModel
from typing import List, Optional

class IngestionStatusResponse(BaseModel):
    filename: str
    status: str
    collection: str
    processed_chunks: int

class UploadResponse(BaseModel):
    filename: str
    collection: str
    message: str

class DeleteResponse(BaseModel):
    filename: str
    message: str
