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
    database_url: str = "sqlite:///./data/whatsapp_ai.db"
    
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
    
    # ElevenLabs
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    
    # Email
    email_host: Optional[str] = None
    email_port: Optional[int] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_use_tls: bool = True
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    ollama_timeout: int = 30
    
    # Chat Settings
    chat_history_limit: int = 50
    chat_default_language: str = "en"
    chat_enable_summary: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file_path: str = "./logs/app.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Storage
    storage_path: str = "./storage"
    max_file_size: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()