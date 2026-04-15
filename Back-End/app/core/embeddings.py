from langchain_huggingface import HuggingFaceEmbeddings
from app.config.settings import settings

class EmbeddingService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    
    def get_embeddings(self):
        return self.embeddings

embedding_service = EmbeddingService()
