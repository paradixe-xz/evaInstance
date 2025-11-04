#!/usr/bin/env python3
"""
Database migration script for Eva.
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import create_tables, init_db
from app.core.settings import get_settings
from app.models import SystemUser
from app.services.auth_service import AuthService
from sqlalchemy.orm import sessionmaker
from app.core.database import engine

def create_admin_user():
    """Create a default admin user."""
    print("Admin user creation skipped - will be created via API endpoints")
    print("Use the /auth/signup endpoint to create your first user")


def main():
    """Run database migrations."""
    print("Starting database migration...")
    
    try:
        # Initialize database
        init_db()
        print("Database tables created successfully")
        
        # Create admin user
        create_admin_user()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()