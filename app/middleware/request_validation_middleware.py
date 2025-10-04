"""
Request validation middleware for input sanitization and rate limiting
"""

import time
from typing import Callable, Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation, rate limiting, and input sanitization
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Rate limiting configuration
        self.rate_limit_requests = 100  # requests per window
        self.rate_limit_window = 60  # window in seconds
        self.rate_limit_storage: Dict[str, deque] = defaultdict(deque)
        
        # Request size limits
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_json_size = 1 * 1024 * 1024  # 1MB for JSON
        
        # Paths exempt from rate limiting
        self.rate_limit_exempt_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        if not self._validate_request_size(request):
            logger.warning(
                "Request size exceeded limit",
                extra={
                    "path": request.url.path,
                    "client_ip": self._get_client_ip(request),
                    "content_length": request.headers.get("content-length", "unknown"),
                }
            )
            raise HTTPException(status_code=413, detail="Request entity too large")
        
        # Apply rate limiting
        if not self._check_rate_limit(request):
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "path": request.url.path,
                    "client_ip": self._get_client_ip(request),
                }
            )
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.rate_limit_window)}
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            if not self._validate_content_type(request):
                logger.warning(
                    "Invalid content type",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "content_type": request.headers.get("content-type", ""),
                        "client_ip": self._get_client_ip(request),
                    }
                )
                raise HTTPException(status_code=415, detail="Unsupported media type")
        
        # Sanitize headers
        self._sanitize_headers(request)
        
        return await call_next(request)
    
    def _validate_request_size(self, request: Request) -> bool:
        """
        Validate request size limits
        """
        content_length = request.headers.get("content-length")
        if not content_length:
            return True
        
        try:
            size = int(content_length)
            
            # Check general request size limit
            if size > self.max_request_size:
                return False
            
            # Check JSON size limit for JSON requests
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type and size > self.max_json_size:
                return False
            
            return True
            
        except ValueError:
            # Invalid content-length header
            return False
    
    def _check_rate_limit(self, request: Request) -> bool:
        """
        Check if request is within rate limits
        """
        path = request.url.path
        
        # Skip rate limiting for exempt paths
        if path in self.rate_limit_exempt_paths:
            return True
        
        # Get client identifier (IP address)
        client_id = self._get_client_ip(request)
        current_time = time.time()
        
        # Get request history for this client
        request_times = self.rate_limit_storage[client_id]
        
        # Remove old requests outside the window
        while request_times and request_times[0] < current_time - self.rate_limit_window:
            request_times.popleft()
        
        # Check if within rate limit
        if len(request_times) >= self.rate_limit_requests:
            return False
        
        # Add current request
        request_times.append(current_time)
        
        return True
    
    def _validate_content_type(self, request: Request) -> bool:
        """
        Validate content type for requests with body
        """
        content_type = request.headers.get("content-type", "")
        
        # Allowed content types
        allowed_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
        ]
        
        # Check if content type is allowed
        for allowed_type in allowed_types:
            if allowed_type in content_type:
                return True
        
        return False
    
    def _sanitize_headers(self, request: Request) -> None:
        """
        Sanitize request headers to prevent injection attacks
        """
        # Headers to remove or sanitize
        dangerous_headers = [
            "x-forwarded-host",
            "x-forwarded-server",
        ]
        
        # Remove potentially dangerous headers
        for header in dangerous_headers:
            if header in request.headers:
                # Note: We can't actually modify request.headers directly in Starlette
                # This is more for logging/monitoring purposes
                logger.debug(
                    "Potentially dangerous header detected",
                    extra={
                        "header": header,
                        "value": request.headers[header],
                        "client_ip": self._get_client_ip(request),
                    }
                )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request
        """
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def cleanup_rate_limit_storage(self) -> None:
        """
        Cleanup old entries from rate limit storage
        This should be called periodically to prevent memory leaks
        """
        current_time = time.time()
        cutoff_time = current_time - self.rate_limit_window * 2  # Keep some buffer
        
        for client_id in list(self.rate_limit_storage.keys()):
            request_times = self.rate_limit_storage[client_id]
            
            # Remove old requests
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
            
            # Remove empty entries
            if not request_times:
                del self.rate_limit_storage[client_id]