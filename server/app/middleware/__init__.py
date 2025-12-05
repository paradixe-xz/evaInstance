"""
Middleware package for the application
"""

from .logging_middleware import LoggingMiddleware

__all__ = [
    "LoggingMiddleware"
]