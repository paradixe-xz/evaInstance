"""
Database initialization script with admin user creation
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import init_db, SessionLocal
from app.models.system_user import SystemUser
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(SystemUser).filter(SystemUser.email == "admin@eva.ai").first()
        
        if admin:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin = SystemUser(
            email="admin@eva.ai",
            name="Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        logger.info("✅ Admin user created successfully")
        logger.info("   Email: admin@eva.ai")
        logger.info("   Password: admin123")
        logger.info("   ⚠️  CHANGE THIS PASSWORD IN PRODUCTION!")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Initialize database and create admin user"""
    print("🔄 Initializing Eva AI Assistant Database...")
    print("=" * 50)
    
    # Initialize database
    print("\n📊 Creating database tables...")
    init_db()
    print("✅ Database tables created")
    
    # Create admin user
    print("\n👤 Creating admin user...")
    create_admin_user()
    
    print("\n" + "=" * 50)
    print("✅ Database initialization complete!")
    print("\n🔐 Default Admin Credentials:")
    print("   Email: admin@eva.ai")
    print("   Password: admin123")
    print("\n⚠️  IMPORTANT: Change the admin password after first login!")
    print("=" * 50)


if __name__ == "__main__":
    main()
