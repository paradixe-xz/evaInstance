#!/usr/bin/env python3
"""
Setup script for the WhatsApp AI Backend
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, cwd=project_root)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment file"""
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created")
        print("⚠️  Please edit .env file with your actual configuration values")
        return True
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        project_root / "logs",
        project_root / "storage" / "media",
        project_root / "data",
        project_root / "migrations"
    ]
    
    print("📁 Creating directories...")
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")

def check_ollama():
    """Check Ollama installation"""
    print("🤖 Checking Ollama installation...")
    try:
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ollama found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama command failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama not found")
        print("   Please install Ollama from: https://ollama.ai/")
        return False

def pull_ollama_model():
    """Pull the default Ollama model"""
    model = os.getenv("OLLAMA_MODEL", "llama2")
    print(f"🤖 Pulling Ollama model: {model}")
    try:
        subprocess.run(["ollama", "pull", model], check=True, timeout=300)
        print(f"✅ Model {model} pulled successfully")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ Failed to pull model {model}: {e}")
        print("   You can pull it manually later: ollama pull " + model)
        return False

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    try:
        from app.core.database import init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 WhatsApp AI Backend Setup")
    print("="*30)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not available yet")
    
    # Check Ollama
    ollama_available = check_ollama()
    if ollama_available:
        pull_ollama_model()
    
    # Initialize database
    initialize_database()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start Ollama service: ollama serve")
    print("3. Run the server: python scripts_new/start_server.py")
    print("   or: python main.py")

if __name__ == "__main__":
    main()