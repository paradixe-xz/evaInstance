"""
Rate limiting middleware for API protection
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        # Store: {key: [(timestamp, count)]}
        self.requests: Dict[str, list] = {}
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()
    
    def _cleanup(self):
        """Remove old entries"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff = current_time - 3600  # Keep last hour
            for key in list(self.requests.keys()):
                self.requests[key] = [
                    (ts, count) for ts, count in self.requests[key]
                    if ts > cutoff
                ]
                if not self.requests[key]:
                    del self.requests[key]
            self.last_cleanup = current_time
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed
        
        Args:
            key: Unique identifier (IP, user_id, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            (is_allowed, retry_after_seconds)
        """
        self._cleanup()
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Get or create request list for this key
        if key not in self.requests:
            self.requests[key] = []
        
        # Filter requests within window
        recent_requests = [
            (ts, count) for ts, count in self.requests[key]
            if ts > cutoff_time
        ]
        
        # Count total requests
        total_requests = sum(count for _, count in recent_requests)
        
        if total_requests >= max_requests:
            # Calculate retry after
            oldest_request = min(ts for ts, _ in recent_requests)
            retry_after = int(window_seconds - (current_time - oldest_request)) + 1
            return False, retry_after
        
        # Add new request
        recent_requests.append((current_time, 1))
        self.requests[key] = recent_requests
        
        return True, None


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations
RATE_LIMITS = {
    "default": {"max_requests": 100, "window": 60},  # 100 req/min
    "auth": {"max_requests": 5, "window": 60},  # 5 req/min for auth
    "chat": {"max_requests": 30, "window": 60},  # 30 req/min for chat
    "analytics": {"max_requests": 20, "window": 60},  # 20 req/min
    "knowledge": {"max_requests": 10, "window": 60},  # 10 req/min for uploads
}


def get_rate_limit_key(request: Request, user_id: Optional[int] = None) -> str:
    """Generate rate limit key from request"""
    if user_id:
        return f"user:{user_id}"
    
    # Use IP address
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    return f"ip:{client_ip}"


def get_rate_limit_config(path: str) -> dict:
    """Get rate limit configuration for path"""
    if "/auth/" in path:
        return RATE_LIMITS["auth"]
    elif "/chat/" in path or "/agents/" in path:
        return RATE_LIMITS["chat"]
    elif "/analytics/" in path:
        return RATE_LIMITS["analytics"]
    elif "/knowledge/" in path:
        return RATE_LIMITS["knowledge"]
    else:
        return RATE_LIMITS["default"]


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    # Skip rate limiting for health checks
    if request.url.path.startswith("/api/v1/health"):
        return await call_next(request)
    
    # Get rate limit config
    config = get_rate_limit_config(request.url.path)
    
    # Get user ID from request state if authenticated
    user_id = getattr(request.state, "user_id", None)
    
    # Generate key
    key = get_rate_limit_key(request, user_id)
    
    # Check rate limit
    is_allowed, retry_after = rate_limiter.is_allowed(
        key=key,
        max_requests=config["max_requests"],
        window_seconds=config["window"]
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Continue with request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(config["max_requests"])
    response.headers["X-RateLimit-Window"] = str(config["window"])
    
    return response
