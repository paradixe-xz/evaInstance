"""
Authentication service
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..core.settings import get_settings
from ..models.system_user import SystemUser
from ..schemas.auth import TokenData

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30


class AuthService:
    """Authentication service"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            email: str = payload.get("email")
            
            if user_id is None:
                return None
            
            token_data = TokenData(user_id=user_id, email=email)
            return token_data
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[SystemUser]:
        """Authenticate user with email and password"""
        user = db.query(SystemUser).filter(SystemUser.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if user.is_locked():
            return None
        
        if not AuthService.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts for 30 minutes
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            db.commit()
            return None
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_user(db: Session, email: str, password: str, name: str, company: Optional[str] = None) -> SystemUser:
        """Create new system user"""
        # Check if user already exists
        existing_user = db.query(SystemUser).filter(SystemUser.email == email).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = AuthService.get_password_hash(password)
        user = SystemUser(
            email=email,
            name=name,
            company=company,
            hashed_password=hashed_password,
            is_verified=True  # Auto-verify for now, can be changed later
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[SystemUser]:
        """Get current user from JWT token"""
        token_data = AuthService.verify_token(token)
        if token_data is None:
            return None
        
        user = db.query(SystemUser).filter(SystemUser.id == token_data.user_id).first()
        if user is None or not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def generate_password_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_password_reset_token(db: Session, token: str) -> Optional[SystemUser]:
        """Verify password reset token"""
        user = db.query(SystemUser).filter(
            SystemUser.password_reset_token == token,
            SystemUser.password_reset_expires > datetime.utcnow()
        ).first()
        
        return user
    
    @staticmethod
    def reset_password(db: Session, user: SystemUser, new_password: str):
        """Reset user password"""
        user.hashed_password = AuthService.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        
        db.commit()
    
    @staticmethod
    def change_password(db: Session, user: SystemUser, current_password: str, new_password: str) -> bool:
        """Change user password"""
        if not AuthService.verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = AuthService.get_password_hash(new_password)
        db.commit()
        
        return True