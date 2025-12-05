#!/usr/bin/env python3
"""
Script de inicio para el backend de Eva AI Assistant
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Función principal para iniciar el servidor"""
    
    # Cambiar al directorio del backend
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🚀 Iniciando Eva AI Assistant Backend...")
    print(f"📁 Directorio: {backend_dir}")
    
    # Verificar que existe el archivo .env
    if not (backend_dir / ".env").exists():
        print("⚠️  Archivo .env no encontrado. Copiando desde .env.example...")
        if (backend_dir / ".env.example").exists():
            subprocess.run(["copy", ".env.example", ".env"], shell=True)
        else:
            print("❌ No se encontró .env.example")
            return
    
    # Iniciar el servidor
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar el servidor: {e}")
    except FileNotFoundError:
        print("❌ uvicorn no encontrado. Instala las dependencias con: pip install -r requirements.txt")

if __name__ == "__main__":
    main()