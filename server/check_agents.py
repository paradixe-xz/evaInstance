"""Script to check agents in the database."""
import sqlite3
from datetime import datetime

def check_agents():
    db_path = 'whatsapp_ai.db'
    print(f"Checking agents in database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if agents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents';")
        if not cursor.fetchone():
            print("❌ Error: 'agents' table does not exist in the database!")
            return
        
        # Get column names
        cursor.execute("PRAGMA table_info(agents)")
        columns = [column[1] for column in cursor.fetchall()]
        print("\n📋 Table columns:", ", ".join(columns))
        
        # Get agent count
        cursor.execute("SELECT COUNT(*) FROM agents")
        count = cursor.fetchone()[0]
        print(f"\n🔢 Total agents in database: {count}")
        
        if count > 0:
            # Get latest agents
            print("\n📝 Latest agents:")
            cursor.execute("""
                SELECT id, name, agent_type, status, 
                       created_at, updated_at, creator_id 
                FROM agents 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                print(f"\n🆔 ID: {row[0]}")
                print(f"📛 Name: {row[1]}")
                print(f"🔧 Type: {row[2]}")
                print(f"📊 Status: {row[3]}")
                print(f"📅 Created: {row[4]}")
                print(f"🔄 Updated: {row[5]}")
                print(f"👤 Creator ID: {row[6]}")
        
        # Check for any foreign key issues
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        if fk_issues:
            print("\n⚠️  Foreign key issues found:", fk_issues)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_agents()
    input("\nPress Enter to exit...")
