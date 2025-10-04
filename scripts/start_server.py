#!/usr/bin/env python3
"""
Startup script for the WhatsApp AI Backend
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_environment_file():
    """Check if .env file exists"""
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env file not found. Please copy .env.example to .env and configure it.")
            print(f"   cp {env_example} {env_file}")
        else:
            print("❌ Neither .env nor .env.example file found")
        return False
    
    print("✅ Environment file found")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        import requests
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Please run: pip install -r requirements.txt")
        return False

def check_ollama_service():
    """Check if Ollama service is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            return True
        else:
            print("⚠️  Ollama service responded with error")
            return False
    except Exception:
        print("⚠️  Ollama service is not running or not accessible")
        print("   Please start Ollama: ollama serve")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        project_root / "logs",
        project_root / "storage" / "media",
        project_root / "data"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")

def initialize_database():
    """Initialize the database"""
    try:
        from app.core.database import init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server"""
    print(f"\n🚀 Starting WhatsApp AI Backend on {host}:{port}")
    print(f"   Reload mode: {'enabled' if reload else 'disabled'}")
    print(f"   Access the API at: http://{host}:{port}")
    print(f"   API Documentation: http://{host}:{port}/docs")
    print("\n" + "="*50)
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🔧 WhatsApp AI Backend Startup Script")
    print("="*40)
    
    # Check system requirements
    check_python_version()
    
    if not check_environment_file():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Check external services (non-blocking)
    ollama_running = check_ollama_service()
    if not ollama_running:
        print("   Note: Server will start without Ollama. Some AI features may not work.")
    
    # Setup directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not found, environment variables may not be loaded")
    
    # Get configuration
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    # Start server
    start_server(host=host, port=port, reload=debug)

if __name__ == "__main__":
    main()