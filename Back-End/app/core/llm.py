from langchain_groq import ChatGroq
from app.config.settings import settings

def get_llm():
    """
    Initialize and return the Groq LLM instance using specific configurations.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=0.0
    )
