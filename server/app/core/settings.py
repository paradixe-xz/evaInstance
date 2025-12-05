"""
Application settings configuration using Pydantic Settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "WhatsApp AI Backend"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./whatsapp_ai.db"
    
    # WhatsApp Business API
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_webhook_secret: str = ""
    whatsapp_api_version: str = "v18.0"
    
    # Twilio (fallback)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout: int = 30
    
    # Chat Settings
    chat_history_limit: int = 50
    chat_default_language: str = "es"
    
    # Logging
    log_level: str = "INFO"
    log_file_path: str = "./logs/app.log"
    
    # Storage
    storage_path: str = "./storage"
    
    # Authentication & Security
    SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings