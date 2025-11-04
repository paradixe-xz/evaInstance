"""
Script to create Knowledge Base tables
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import get_database_url
from app.core.database import Base
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.agent import Agent

def create_knowledge_tables():
    """Create Knowledge Base tables"""
    try:
        # Create engine
        engine = create_engine(get_database_url())
        
        print("Creating Knowledge Base tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Knowledge Base tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('knowledge_documents', 'knowledge_chunks')
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if 'knowledge_documents' in tables:
                print("✅ knowledge_documents table created")
            else:
                print("❌ knowledge_documents table not found")
                
            if 'knowledge_chunks' in tables:
                print("✅ knowledge_chunks table created")
            else:
                print("❌ knowledge_chunks table not found")
        
        print("\n📊 Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_knowledge_tables()
    if success:
        print("\n🎉 Knowledge Base setup completed!")
    else:
        print("\n💥 Knowledge Base setup failed!")
        sys.exit(1)