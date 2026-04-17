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
    JWT_EXPIRY_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRY_DAYS: int = Field(default=7)
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
