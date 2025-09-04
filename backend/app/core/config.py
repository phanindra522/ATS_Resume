from pydantic_settings import BaseSettings
from typing import Optional
import os
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "ats_scoring"
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    
    # Security - Now loaded from .env
    SECRET_KEY: str = ""  # This will be overridden by .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx"]
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # Options: openai, gemini, anthropic, local
    LLM_PROVIDER_API_KEY: str = ""
    LLM_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536  # OpenAI ada-002 embedding dimension
    
   
    
    class Config:
        env_file = ".env"
        # This ensures .env values override defaults
        env_file_encoding = 'utf-8'
    
    def get_llm_provider(self) -> LLMProvider:
        """Get the configured LLM provider"""
        try:
            return LLMProvider(self.LLM_PROVIDER.lower())
        except ValueError:
            return LLMProvider.OPENAI  # Default fallback
    
    def is_llm_configured(self) -> bool:
        """Check if LLM provider is properly configured"""
        return bool(self.LLM_PROVIDER_API_KEY)
    
    def get_llm_config_info(self) -> dict:
        """Get LLM configuration information for debugging"""
        return {
            "provider": self.LLM_PROVIDER,
            "api_key_configured": bool(self.LLM_PROVIDER_API_KEY),
            "is_configured": self.is_llm_configured()
        }

settings = Settings()