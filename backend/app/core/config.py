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
    LLM_PROVIDER: str = "gemini"  # Options: openai, gemini, anthropic, local
    LLM_PROVIDER_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.0-flash-lite"  # LLM model for text generation (e.g., gpt-3.5-turbo, gemini-2.0-flash-lite)
    LLM_EMBEDDING_MODEL: str = "text-embedding-004"  # Embedding model (e.g., text-embedding-ada-002, text-embedding-004)
    EMBEDDING_DIMENSION: int = 768  # Embedding dimension (1536 for OpenAI, 768 for Gemini)
    
    # LLM Enhancement Flags for Multi-Agent System
    USE_LLM_FOR_KEYWORDS: bool = False     # Disable LLM for keyword extraction to avoid quota issues
    USE_LLM_FOR_SKILLS: bool = False       # Disable LLM for skill normalization to avoid quota issues
    USE_LLM_FOR_EXPERIENCE: bool = False   # Enable LLM for experience analysis
    USE_LLM_FOR_EDUCATION: bool = False    # Enable LLM for education analysis
    
    # LLM Fallback Settings
    LLM_FALLBACK_ENABLED: bool = True      # Enable fallback to rule-based when LLM fails
    LLM_TIMEOUT_SECONDS: int = 30          # Increased timeout for LLM API calls
    LLM_RETRY_ATTEMPTS: int = 3            # Increased retry attempts for failed LLM calls
    
   
    
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