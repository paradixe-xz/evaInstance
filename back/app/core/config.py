"""
Core configuration management for the WhatsApp AI Backend
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    app_name: str = Field(default="WhatsApp AI Backend", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database Settings
    database_url: str = Field(default="sqlite:///./whatsapp_ai.db", env="DATABASE_URL")
    
    # WhatsApp Business API Settings
    whatsapp_access_token: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_business_account_id: str = Field(..., env="WHATSAPP_BUSINESS_ACCOUNT_ID")
    whatsapp_verify_token: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")
    whatsapp_webhook_secret: Optional[str] = Field(default=None, env="WHATSAPP_WEBHOOK_SECRET")
    whatsapp_api_version: str = Field(default="v18.0", env="WHATSAPP_API_VERSION")
    
    # Ollama Settings
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="ana", env="OLLAMA_MODEL")
    ollama_system_prompt: str = Field(default="You are Ana, a helpful AI assistant for WhatsApp conversations.", env="OLLAMA_SYSTEM_PROMPT")
    ollama_temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")
    ollama_max_tokens: int = Field(default=2000, env="OLLAMA_MAX_TOKENS")
    ollama_timeout: int = Field(default=30, env="OLLAMA_TIMEOUT")
    
    # Knowledge Base Settings
    knowledge_base_path: str = Field(default="./data/knowledge_base", env="KNOWLEDGE_BASE_PATH")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    max_search_results: int = Field(default=5, env="MAX_SEARCH_RESULTS")
    
    # Chat Settings
    max_conversation_history: int = Field(default=50, env="MAX_CONVERSATION_HISTORY")
    chat_session_timeout: int = Field(default=3600, env="CHAT_SESSION_TIMEOUT")  # 1 hour

    # Email / Resend Settings
    email_service_url: str = Field(default="http://localhost:4000", env="EMAIL_SERVICE_URL")
    resend_from_email: str = Field(default="assistant@yourdomain.com", env="RESEND_FROM_EMAIL")
    resend_inbound_secret: Optional[str] = Field(default=None, env="RESEND_INBOUND_SECRET")

    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Security Settings
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    # Storage Settings
    data_directory: str = Field(default="./data", env="DATA_DIRECTORY")
    chat_history_directory: str = Field(default="./data/chat_history", env="CHAT_HISTORY_DIRECTORY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_whatsapp_api_url() -> str:
    """Get WhatsApp API base URL"""
    return f"https://graph.facebook.com/{settings.whatsapp_api_version}"


def get_database_url() -> str:
    """Get database URL"""
    return settings.database_url


def is_production() -> bool:
    """Check if running in production mode"""
    return not settings.debug


def get_cors_origins() -> list:
    """Get CORS origins as a list"""
    if settings.cors_origins == "*":
        return ["*"]
    return [origin.strip() for origin in settings.cors_origins.split(",")]


def get_ollama_url() -> str:
    """Get Ollama base URL"""
    return settings.ollama_base_url


def get_knowledge_base_path() -> str:
    """Get knowledge base storage path"""
    return settings.knowledge_base_path


def get_max_file_size_bytes() -> int:
    """Get maximum file size in bytes"""
    return settings.max_file_size_mb * 1024 * 1024