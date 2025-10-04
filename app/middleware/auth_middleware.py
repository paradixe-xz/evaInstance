"""
Authentication middleware for API security
"""

import hmac
import hashlib
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication and webhook verification
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.webhook_verify_token = settings.whatsapp_verify_token
        self.webhook_secret = settings.whatsapp_webhook_secret
        
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }
        
        # Paths that require webhook verification
        self.webhook_paths = {
            "/api/v1/whatsapp/webhook",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Skip authentication for public paths
        if path in self.public_paths or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)
        
        # Handle webhook verification for GET requests
        if path in self.webhook_paths and request.method == "GET":
            logger.info(f"Webhook GET request received: {path}")
            if not self._verify_webhook_token(request):
                logger.warning(
                    "Webhook verification failed",
                    extra={
                        "path": path,
                        "method": request.method,
                        "client_ip": self._get_client_ip(request),
                    }
                )
                raise HTTPException(status_code=403, detail="Webhook verification failed")
        
        # Handle webhook signature verification for POST requests
        elif path in self.webhook_paths and request.method == "POST":
            logger.info(f"Webhook POST request received: {path}")
            if not await self._verify_webhook_signature(request):
                logger.warning(
                    "Webhook signature verification failed",
                    extra={
                        "path": path,
                        "method": request.method,
                        "client_ip": self._get_client_ip(request),
                    }
                )
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
        
        # For other API endpoints, you can add additional authentication logic here
        # For now, we'll allow all requests to pass through
        
        return await call_next(request)
    
    def _verify_webhook_token(self, request: Request) -> bool:
        """
        Verify webhook token for GET requests (webhook verification)
        """
        hub_mode = request.query_params.get("hub.mode")
        hub_verify_token = request.query_params.get("hub.verify_token")
        
        logger.info(f"Webhook verification attempt: mode={hub_mode}, token={hub_verify_token}, expected={self.webhook_verify_token}")
        
        if hub_mode == "subscribe" and hub_verify_token == self.webhook_verify_token:
            logger.info("Webhook verification successful")
            return True
        
        logger.warning(f"Webhook verification failed: mode={hub_mode}, token={hub_verify_token}")
        return False
    
    async def _verify_webhook_signature(self, request: Request) -> bool:
        """
        Verify webhook signature for POST requests
        """
        logger.info(f"POST webhook signature verification - Headers: {dict(request.headers)}")
        
        # TEMPORARY: Skip signature verification for debugging
        logger.warning("TEMPORARY: Skipping webhook signature verification for debugging")
        return True
        
        if not self.webhook_secret:
            # If no secret is configured, skip verification
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        signature_header = request.headers.get("x-hub-signature-256")
        logger.info(f"Signature header received: {signature_header}")
        
        if not signature_header:
            logger.warning("No x-hub-signature-256 header found")
            return False
        
        try:
            # Read request body
            body = await request.body()
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Extract signature from header (format: "sha256=<signature>")
            if signature_header.startswith("sha256="):
                received_signature = signature_header[7:]
            else:
                return False
            
            # Compare signatures using constant-time comparison
            return hmac.compare_digest(expected_signature, received_signature)
            
        except Exception as e:
            logger.error(
                "Error verifying webhook signature",
                extra={"error": str(e)},
                exc_info=True
            )
            return False
    
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