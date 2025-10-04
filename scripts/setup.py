#!/usr/bin/env python3
"""
Setup script for the WhatsApp AI Backend
"""

import os
import sys
import subprocess
from pathlib import Path
import venv

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_virtual_environment():
    """Create virtual environment if needed"""
    venv_path = project_root / "venv"
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return venv_path
    
    print("🔧 Creating virtual environment...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created")
        return venv_path
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return None

def get_venv_python(venv_path):
    """Get the Python executable from virtual environment"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Linux/Mac
        return venv_path / "bin" / "python"

def get_venv_pip(venv_path):
    """Get the pip executable from virtual environment"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "pip.exe"
    else:  # Linux/Mac
        return venv_path / "bin" / "pip"

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Check if we're in an externally managed environment
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--dry-run", "requests"], 
                              capture_output=True, text=True, cwd=project_root)
        externally_managed = "externally-managed-environment" in result.stderr
    except:
        externally_managed = True
    
    if externally_managed:
        print("⚠️  Detected externally managed environment, using virtual environment...")
        venv_path = create_virtual_environment()
        if not venv_path:
            return False
        
        python_exe = get_venv_python(venv_path)
        pip_exe = get_venv_pip(venv_path)
        
        # Upgrade pip first
        try:
            subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], 
                          check=True, cwd=project_root)
        except subprocess.CalledProcessError:
            print("⚠️  Could not upgrade pip, continuing...")
        
        # Install dependencies
        try:
            subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], 
                          check=True, cwd=project_root)
            print("✅ Dependencies installed successfully in virtual environment")
            
            # Create activation script
            create_activation_script(venv_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    else:
        # Standard installation
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          check=True, cwd=project_root)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

def create_activation_script(venv_path):
    """Create activation script for easy use"""
    if os.name == 'nt':  # Windows
        activate_script = project_root / "activate.bat"
        content = f"""@echo off
call "{venv_path}\\Scripts\\activate.bat"
echo Virtual environment activated!
echo To run the server: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
    else:  # Linux/Mac
        activate_script = project_root / "activate.sh"
        content = f"""#!/bin/bash
source "{venv_path}/bin/activate"
echo "Virtual environment activated!"
echo "To run the server: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
"""
    
    activate_script.write_text(content)
    if not os.name == 'nt':
        os.chmod(activate_script, 0o755)
    
    print(f"✅ Activation script created: {activate_script}")
    print(f"   Run: {'activate.bat' if os.name == 'nt' else './activate.sh'}")

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