"""
Database configuration and connection management
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from .config import get_settings

settings = get_settings()

# Create database engine
if settings.database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Disable SQLAlchemy logging
    )
else:
    # PostgreSQL or other database configuration
    engine = create_engine(
        settings.database_url,
        echo=False  # Disable SQLAlchemy logging
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def create_tables():
    """Create all database tables"""
    # Import all models to ensure they are registered with Base
    from app.models import (
        User, ChatSession, Message, SystemUser, 
        Campaign, Agent, CallLog
    )
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database"""
    # Create data directory if it doesn't exist
    os.makedirs(settings.data_directory, exist_ok=True)
    
    # Create tables
    create_tables()
    
    print(f"Database initialized at: {settings.database_url}")


def close_db():
    """Close database connections"""
    engine.dispose()