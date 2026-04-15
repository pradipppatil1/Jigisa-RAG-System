import logging
from typing import Optional, List, Dict, Any
from qdrant_client.http import models

from app.guardrails.service import guardrail_service
from app.routing.service import routing_service
from app.core.vector_store import vector_store
from app.core.llm import get_llm
from app.chat.schemas import ChatResponse
from app.chat.history_service import history_service

logger = logging.getLogger(__name__)

class ChatService:
    def process_query(self, query: str, user_id: int, username: str, role: str, session_id: Optional[str] = None) -> ChatResponse:
        str_user_id = str(user_id)
        
        # 0. Session Management
        if not session_id:
            session_id = history_service.create_session(user_id=user_id, initial_query=query)
            
        # 1. Input Validation
        logger.info(f"Starting query processing for user {username} (Role: {role}), Session: {session_id}")
        input_validation = guardrail_service.validate_input(
            query=query, 
            user_id=str_user_id, 
            user_role=role
        )
        
        input_warnings = [c.message for c in input_validation.checks if c.status == "warning" and c.message]
        
        if input_validation.status == "blocked":
            blocked_msg = "Query blocked by security policies."
            for check in input_validation.checks:
                if check.status == "blocked" and check.message:
                    blocked_msg = check.message
                    break
            # Save blocked user message
            history_service.add_message(session_id, "user", query, warnings=input_warnings)
            history_service.add_message(session_id, "assistant", blocked_msg, warnings=input_warnings)
            return ChatResponse(
                answer=blocked_msg,
                session_id=session_id,
                input_warnings=input_warnings
            )
            
        # 2. Semantic Routing & RBAC
        routing_result = routing_service.route_query(
            query=query,
            user_role=role,
            user_id=str_user_id
        )
        
        if not routing_result.is_authorized:
            msg = routing_result.message or "Unauthorized cross-department access detected."
            history_service.add_message(session_id, "user", query, warnings=input_warnings)
            history_service.add_message(session_id, "assistant", msg, route_name=routing_result.route_name, warnings=input_warnings)
            return ChatResponse(
                answer=msg,
                session_id=session_id,
                route_name=routing_result.route_name,
                confidence=routing_result.confidence,
                input_warnings=input_warnings
            )
            
        collections = routing_result.collections
        
        # 3. Retrieval
        if not collections:
            msg = "No document collections available to search for your role."
            history_service.add_message(session_id, "user", query, warnings=input_warnings)
            history_service.add_message(session_id, "assistant", msg, route_name=routing_result.route_name, warnings=input_warnings)
            return ChatResponse(
                answer=msg,
                session_id=session_id,
                route_name=routing_result.route_name,
                confidence=routing_result.confidence,
                input_warnings=input_warnings
            )
            
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.collection",
                    match=models.MatchAny(any=collections)
                ),
                models.FieldCondition(
                    key="metadata.access_roles",
                    match=models.MatchAny(any=[role])
                )
            ]
        )
        
        try:
            docs = vector_store.vector_store.similarity_search(
                query=query, 
                k=5, 
                filter=filter_condition
            )
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            docs = []
            
        retrieved_chunks = []
        context_parts = []
        for d in docs:
            chunk_dict = dict(d.metadata)
            chunk_dict["text"] = d.page_content
            retrieved_chunks.append(chunk_dict)
            
            src = chunk_dict.get("source_document", "Unknown Source")
            page = chunk_dict.get("page_number", "N/A")
            context_parts.append(f"[Source: {src}, Page {page}]\n{d.page_content}")
            
        context_str = "\n\n".join(context_parts)
        
        # Fetch conversation summary context
        chat_summary = history_service.get_summary(session_id)
        summary_text = f"Previous Conversation Summary:\n{chat_summary}\n\n" if chat_summary else ""

        # 4. LLM Generation
        prompt = f"""You are FinBot, a professional AI assistant for FinSolve Technologies.
Answer the question based ONLY on the provided context. If the context does not contain the answer, say "I cannot answer this based on the available documentation."
Whenever you use information from the context, YOU MUST cite your sources explicitly in your text using the format [Source: filename, Page X].

{summary_text}Context:
{context_str}

Question: {query}
Answer:"""

        llm = get_llm()
        try:
            llm_response = llm.invoke(prompt)
            answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            answer = "Sorry, there was an error generating a response at this time."
            
        # 5. Output Validation
        output_validation = guardrail_service.validate_output(
            response=answer,
            retrieved_chunks=retrieved_chunks,
            user_role=role,
            user_id=str_user_id,
            query=query
        )
        
        if output_validation.status == "blocked":
            blocked_msg = "The generated response was blocked by output security policies."
            for check in output_validation.checks:
                if check.status == "blocked" and check.message:
                    blocked_msg = check.message
                    break
            history_service.add_message(session_id, "user", query, warnings=input_warnings)
            history_service.add_message(session_id, "assistant", blocked_msg, route_name=routing_result.route_name, warnings=input_warnings)
            return ChatResponse(
                answer=blocked_msg,
                session_id=session_id,
                route_name=routing_result.route_name,
                confidence=routing_result.confidence,
                input_warnings=input_warnings
            )
            
        all_warnings = input_warnings + output_validation.warnings
        
        source_documents = [
            {"source": d.metadata.get("source_document"), "page": d.metadata.get("page_number")}
            for d in docs
        ]
        
        # Save successful interaction
        history_service.add_message(session_id, "user", query, warnings=input_warnings)
        history_service.add_message(session_id, "assistant", answer, citations=source_documents, route_name=routing_result.route_name, warnings=all_warnings)
        
        return ChatResponse(
            answer=answer,
            session_id=session_id,
            source_documents=source_documents,
            route_name=routing_result.route_name,
            confidence=routing_result.confidence,
            guardrail_warnings=all_warnings
        )

chat_service = ChatService()
