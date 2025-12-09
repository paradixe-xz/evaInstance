
import sqlite3
import os

def check_and_fix_db():
    db_path = "whatsapp_ai.db"
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "ai_paused" not in columns:
            print("Adding missing column 'ai_paused' to 'users' table...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN ai_paused BOOLEAN DEFAULT 0")
                conn.commit()
                print("Successfully added 'ai_paused' column.")
            except Exception as e:
                print(f"Error adding column: {e}")
        else:
            print("Column 'ai_paused' already exists.")
            
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_and_fix_db()
