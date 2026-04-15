import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.chat_history import ChatSession, ChatMessage
from app.core.llm import get_llm
from app.core.database import SessionLocal

class HistoryService:

    def create_session(self, user_id: int, initial_query: str) -> str:
        db: Session = SessionLocal()
        try:
            session_id = str(uuid.uuid4())
            title = initial_query[:30] + "..." if len(initial_query) > 30 else initial_query
            session = ChatSession(id=session_id, user_id=user_id, title=title, summary="")
            db.add(session)
            db.commit()
            return session_id
        finally:
            db.close()

    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        citations: Optional[List[dict]] = None, 
        route_name: Optional[str] = None, 
        warnings: Optional[List[str]] = None
    ):
        db: Session = SessionLocal()
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                citations=citations or [],
                route_name=route_name,
                warnings=warnings or []
            )
            db.add(message)
            db.commit()
            
            # If it's an assistant response, trigger summary update
            if role == "assistant":
                # Need memory to update summary. Look up the last user query as well.
                # Simplification: we fetch the last two messages
                last_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(desc(ChatMessage.created_at)).limit(2).all()
                if len(last_msgs) == 2:
                    m1, m2 = last_msgs[1], last_msgs[0] # User then Assistant
                    if m1.role == 'user' and m2.role == 'assistant':
                        self._update_summary(session_id, m1.content, m2.content, db)
        finally:
            db.close()

    def _update_summary(self, session_id: str, user_query: str, assistant_response: str, db: Session):
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session: return

        current_summary = session.summary or "No summary yet."
        
        prompt = f"""You are a chat memory summarizer. 
Progressively update the conversation summary incorporating the new turn of conversation.
Return ONLY the updated summary text.

Current summary:
{current_summary}

New turn:
Human: {user_query}
AI: {assistant_response}

Updated Summary:"""

        try:
            llm = get_llm()
            llm_response = llm.invoke(prompt)
            new_summary = llm_response.content.strip() if hasattr(llm_response, 'content') else str(llm_response).strip()
            session.summary = new_summary
            db.commit()
        except Exception as e:
            # We don't fail the message addition if summarization fails
            import logging
            logging.error(f"Error updating summary for {session_id}: {e}")

    def get_summary(self, session_id: str) -> str:
        db: Session = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session and session.summary:
                return session.summary
            return ""
        finally:
            db.close()

    def get_user_sessions(self, user_id: int):
        db: Session = SessionLocal()
        try:
            # Order using coalesce so that logic sorts by updated_at or created_at
            from sqlalchemy import func
            sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(desc(func.coalesce(ChatSession.updated_at, ChatSession.created_at))).all()
            return [{"id": s.id, "title": s.title, "updated_at": s.updated_at or s.created_at} for s in sessions]
        finally:
            db.close()

    def get_session_messages(self, session_id: str, user_id: int):
        db: Session = SessionLocal()
        try:
            # verify ownership
            session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
            if not session:
                return None
            
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at).all()
            
            res = []
            for m in messages:
                res.append({
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "citations": m.citations,
                    "route_name": m.route_name,
                    "warnings": m.warnings,
                    "created_at": m.created_at
                })
            return {"session": {"id": session.id, "title": session.title, "summary": session.summary}, "messages": res}
        finally:
            db.close()

    def delete_session(self, session_id: str, user_id: int) -> bool:
        db: Session = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
            if session:
                db.delete(session)
                db.commit()
                return True
            return False
        finally:
            db.close()

history_service = HistoryService()
