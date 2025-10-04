"""
Custom exceptions for the WhatsApp AI Backend
"""

from typing import Any, Dict, Optional


class WhatsAppAIException(Exception):
    """Base exception for WhatsApp AI Backend"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(WhatsAppAIException):
    """Raised when there's a configuration error"""
    pass


class DatabaseError(WhatsAppAIException):
    """Raised when there's a database error"""
    pass


class WhatsAppAPIError(WhatsAppAIException):
    """Raised when there's a WhatsApp API error"""
    pass


class OllamaError(WhatsAppAIException):
    """Raised when there's an Ollama AI error"""
    pass


class ChatHistoryError(WhatsAppAIException):
    """Raised when there's a chat history error"""
    pass


class ValidationError(WhatsAppAIException):
    """Raised when there's a validation error"""
    pass


class AuthenticationError(WhatsAppAIException):
    """Raised when there's an authentication error"""
    pass


class RateLimitError(WhatsAppAIException):
    """Raised when rate limit is exceeded"""
    pass


class ServiceUnavailableError(WhatsAppAIException):
    """Raised when a service is unavailable"""
    pass