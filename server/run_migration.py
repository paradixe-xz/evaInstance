"""
Database migration script to add missing columns to agents table.
"""
import os
import sqlite3
from sqlalchemy import create_engine

def add_missing_columns():
    # Database URL - using whatsapp_ai.db which was found in the directory
    db_path = os.path.join(os.path.dirname(__file__), 'whatsapp_ai.db')
    db_url = f'sqlite:///{db_path}'
    
    print(f"Connecting to database at: {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of columns to add if they don't exist
    columns_to_add = [
        'workflow_steps',
        'conversation_structure',
        'ollama_model_name',
        'modelfile_content',
        'custom_template',
        'ollama_parameters',
        'personality_traits'
    ]
    
    try:
        # Get existing columns
        cursor.execute("PRAGMA table_info(agents)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        for column in columns_to_add:
            if column not in existing_columns:
                # Determine column type based on name
                if column in ['workflow_steps', 'conversation_structure', 'ollama_parameters', 'personality_traits']:
                    col_type = 'TEXT'  # SQLite stores JSON as TEXT
                elif column == 'ollama_model_name':
                    col_type = 'VARCHAR(100)'
                elif column in ['modelfile_content', 'custom_template']:
                    col_type = 'TEXT'
                else:
                    col_type = 'TEXT'
                
                # Add the column
                sql = f"ALTER TABLE agents ADD COLUMN {column} {col_type} DEFAULT NULL;"
                print(f"Executing: {sql}")
                cursor.execute(sql)
                print(f"✓ Added column: {column}")
            else:
                print(f"✓ Column already exists: {column}")
        
        # Commit changes
        conn.commit()
        print("\n✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    add_missing_columns()
    print("\nMigration completed. Press Enter to exit...")
    input()
