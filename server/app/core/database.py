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
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
            "isolation_level": None,
            "detect_types": 1  # Enable type detection
        },
        poolclass=StaticPool,
        echo=True  # Enable SQLAlchemy logging for debugging
    )
else:
    # PostgreSQL or other database configuration
    engine = create_engine(
        settings.database_url,
        echo=True,  # Enable SQLAlchemy logging for debugging
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10,
        future=True
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def create_tables():
    """Create all database tables"""
    try:
        # Import all models to ensure they are registered with Base
        from app.models import (
            User, ChatSession, Message, SystemUser, 
            Campaign, Agent, CallLog, SIPTrunk,
            KnowledgeDocument, KnowledgeChunk
        )
        
        print("🔍 Verificando tablas en la base de datos...")
        print(f"🔗 URL de la base de datos: {settings.database_url}")
        
        # Create all tables
        print("🔄 Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Tablas en la base de datos: {tables}")
        
    except Exception as e:
        print(f"❌ Error al crear las tablas: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise


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