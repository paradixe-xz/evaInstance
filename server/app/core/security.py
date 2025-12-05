"""
Security utilities for password hashing and JWT tokens
"""
from ..services.auth_service import AuthService

# Export password hashing functions
get_password_hash = AuthService.get_password_hash
verify_password = AuthService.verify_password

# Export JWT functions
create_access_token = AuthService.create_access_token
verify_token = AuthService.verify_token

__all__ = [
    'get_password_hash',
    'verify_password',
    'create_access_token',
    'verify_token'
]
