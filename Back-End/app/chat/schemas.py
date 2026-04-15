from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: Optional[str] = None
    source_documents: Optional[List[Dict[str, Any]]] = []
    route_name: Optional[str] = None
    confidence: Optional[float] = 0.0
    guardrail_warnings: Optional[List[str]] = []
    input_warnings: Optional[List[str]] = []

class ChatSessionListItem(BaseModel):
    id: str
    title: str
    updated_at: Optional[datetime] = None

class ChatMessageItem(BaseModel):
    id: int
    role: str
    content: str
    citations: Optional[List[Dict[str, Any]]] = []
    route_name: Optional[str] = None
    warnings: Optional[List[str]] = []
    created_at: datetime

class ChatSessionDetailResponse(BaseModel):
    session: Dict[str, Any]
    messages: List[ChatMessageItem]
