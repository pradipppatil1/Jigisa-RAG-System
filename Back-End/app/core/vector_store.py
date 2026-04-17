from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config.settings import settings
from app.core.embeddings import embedding_service

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self.collection_name = settings.COLLECTION_NAME
        
        # Ensure collection exists before initializing vector store
        if not self.client.collection_exists(self.collection_name):
            embedding_dim = len(embedding_service.get_embeddings().embed_query("test"))
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=embedding_dim, distance=models.Distance.COSINE),
            )
            
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=embedding_service.get_embeddings()
        )
        self._ensure_payload_indexes()

    def _ensure_payload_indexes(self):
        for field in ["collection", "access_roles", "source_document"]:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass
        # Enable full-text search on page_content for keyword fallback retrieval
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="page_content",
                field_schema=models.TextIndexParams(
                    type="text",
                    tokenizer=models.TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=30,
                    lowercase=True,
                ),
            )
        except Exception:
            pass

    def add_documents(self, documents: list):
        self.vector_store.add_documents(documents)

    def keyword_search(
        self,
        keywords: list[str],
        collection_filter: list[str],
        role_filter: str,
        limit: int = 3,
    ) -> list:
        """Scroll Qdrant for documents whose page_content contains any of the keywords."""
        keyword_conditions = [
            models.FieldCondition(
                key="page_content",
                match=models.MatchText(text=kw)
            )
            for kw in keywords
        ]
        combined_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.collection",
                    match=models.MatchAny(any=collection_filter)
                ),
                models.FieldCondition(
                    key="metadata.access_roles",
                    match=models.MatchAny(any=[role_filter])
                ),
            ],
            should=keyword_conditions,
        )
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=combined_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return results

    def delete_by_filename(self, filename: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.source_document",
                            match=models.MatchValue(value=filename)
                        )
                    ]
                )
            )
        )

vector_store = VectorStore()
