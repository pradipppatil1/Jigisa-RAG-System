from app.guardrails.service import guardrail_service
from app.routing.service import routing_service
from app.core.vector_store import vector_store
from app.core.llm import get_llm
from qdrant_client.http import models

class AblationRunner:
    def __init__(self):
        self.llm = get_llm()

    def run_query(self, query: str, user_role: str, 
                  use_routing: bool, use_rbac: bool, use_guardrails: bool) -> dict:
        str_user_id = "eval_user"
        
        # 1. Input Guardrails
        if use_guardrails:
            input_validation = guardrail_service.validate_input(query=query, user_id=str_user_id, user_role=user_role)
            if input_validation.status == "blocked":
                return {"answer": "Blocked by input guardrails", "contexts": []}

        # 2. Routing
        route_name = None
        collections = []
        if use_routing:
            routing_result = routing_service.route_query(query=query, user_role=user_role, user_id=str_user_id)
            route_name = routing_result.route_name
            if use_rbac:
                if not routing_result.is_authorized:
                    return {"answer": "Unauthorized cross-department access detected.", "contexts": []}
                collections = routing_result.collections
            else:
                # Routing ON, RBAC OFF: Determine collections based on intent, ignore role restrictions.
                from app.routing.service import ROUTE_COLLECTION_MAP
                collections = ROUTE_COLLECTION_MAP.get(route_name, [])

        # 3. Retrieval
        filter_condition = None
        if use_routing and collections:
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="collection",
                        match=models.MatchAny(any=collections)
                    )
                ]
            )
        elif use_rbac and not use_routing:
             user_collections = routing_service._get_user_collections(user_role)
             filter_condition = models.Filter(
                must=[
                    models.FieldCondition(key="collection", match=models.MatchAny(any=list(user_collections)))
                ]
             )
             
        try:
            if filter_condition:
                docs = vector_store.vector_store.similarity_search(query=query, k=5, filter=filter_condition)
            else:
                docs = vector_store.vector_store.similarity_search(query=query, k=5) # Global unbounded search
        except Exception:
             docs = []

        retrieved_chunks = []
        context_parts = []
        for d in docs:
            chunk_dict = dict(d.metadata)
            chunk_dict["text"] = d.page_content
            retrieved_chunks.append(chunk_dict)
            context_parts.append(d.page_content)
            
        context_str = "\n\n".join(context_parts)

        # 4. LLM Generation
        prompt = f"""You are FinBot. Answer the question based ONLY on the provided context. If the context does not contain the answer, say "I cannot answer this based on the available documentation."

Context:
{context_str}

Question: {query}
Answer:"""

        try:
            ans = self.llm.invoke(prompt)
            answer = ans.content if hasattr(ans, 'content') else str(ans)
        except Exception:
            answer = "Error generating response"

        # 5. Output Guardrails
        if use_guardrails:
            out_val = guardrail_service.validate_output(
                response=answer,
                retrieved_chunks=retrieved_chunks,
                user_role=user_role,
                user_id=str_user_id,
                query=query
            )
            if out_val.status == "blocked":
                answer = "Blocked by output guardrails"

        return {
            "answer": answer,
            "contexts": context_parts
        }

runner = AblationRunner()
