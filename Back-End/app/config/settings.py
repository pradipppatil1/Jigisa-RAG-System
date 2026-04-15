from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    EMBEDDING_MODEL_NAME: str
    COLLECTION_NAME: str
    RAW_DATA_PATH: str

    # MySQL
    MYSQL_DATABASE_URL: str

    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str
    GUARDRAILS_GROQ_MODEL: str
    
    # JWT Auth
    JWT_SECRET_KEY: str
    JWT_EXPIRY_HOURS: int = Field(default=24)
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
