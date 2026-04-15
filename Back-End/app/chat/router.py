from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.chat.schemas import ChatRequest, ChatResponse, ChatSessionListItem, ChatSessionDetailResponse
from app.chat.service import chat_service
from app.chat.history_service import history_service
from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/query", response_model=ChatResponse)
def query_rag(request: ChatRequest, current_user: CurrentUser = Depends(get_current_user)):
    """
    Process a user query through the full RAG pipeline (Guardrails -> Router -> Retrieval -> LLM).
    """
    return chat_service.process_query(
        query=request.query,
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
        session_id=request.session_id
    )

@router.get("/sessions", response_model=List[ChatSessionListItem])
def get_sessions(current_user: CurrentUser = Depends(get_current_user)):
    """Retrieve all chat sessions for the current user."""
    return history_service.get_user_sessions(current_user.user_id)

@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_session_history(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Retrieve the full message history for a specific session."""
    data = history_service.get_session_messages(session_id, current_user.user_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
    return data

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Delete a chat session and all its messages."""
    success = history_service.delete_session(session_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
    return {"status": "success", "message": "Session deleted successfully"}
