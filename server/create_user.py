#!/usr/bin/env python3
"""
Script CLI para crear usuarios administradores
Uso: python create_user.py
"""

import sys
import os
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import get_db_context
from app.repositories.user_repository import UserRepository
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_admin_user():
    """Create a new admin user interactively"""
    print("\n" + "="*50)
    print("🔐 CREAR NUEVO USUARIO ADMINISTRADOR")
    print("="*50 + "\n")
    
    # Get user input
    email = input("📧 Email: ").strip()
    if not email:
        print("❌ Email es requerido")
        return
    
    username = input("👤 Username: ").strip()
    if not username:
        print("❌ Username es requerido")
        return
    
    full_name = input("📝 Nombre completo (opcional): ").strip() or None
    
    # Get password with confirmation
    while True:
        password = getpass("🔑 Contraseña: ")
        if not password:
            print("❌ Contraseña es requerida")
            continue
        
        if len(password) < 6:
            print("❌ La contraseña debe tener al menos 6 caracteres")
            continue
            
        password_confirm = getpass("🔑 Confirmar contraseña: ")
        
        if password != password_confirm:
            print("❌ Las contraseñas no coinciden. Intenta de nuevo.\n")
            continue
        
        break
    
    # Create user
    try:
        with get_db_context() as db:
            user_repo = UserRepository(db)
            
            # Check if user already exists
            existing_user = user_repo.get_by_email(email)
            if existing_user:
                print(f"\n❌ Ya existe un usuario con el email: {email}")
                return
            
            existing_user = user_repo.get_by_username(username)
            if existing_user:
                print(f"\n❌ Ya existe un usuario con el username: {username}")
                return
            
            # Create user
            hashed_password = get_password_hash(password)
            user = user_repo.create_user(
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True,
                is_superuser=True  # Admin user
            )
            
            print("\n" + "="*50)
            print("✅ USUARIO CREADO EXITOSAMENTE")
            print("="*50)
            print(f"\n📧 Email: {user.email}")
            print(f"👤 Username: {user.username}")
            if user.full_name:
                print(f"📝 Nombre: {user.full_name}")
            print(f"🔑 ID: {user.id}")
            print(f"👑 Admin: Sí")
            print("\n✨ El usuario puede iniciar sesión ahora.\n")
            
    except Exception as e:
        print(f"\n❌ Error al crear usuario: {str(e)}")
        logger.error(f"Error creating user: {e}")


def list_users():
    """List all existing users"""
    try:
        with get_db_context() as db:
            user_repo = UserRepository(db)
            users = user_repo.list_users()
            
            if not users:
                print("\n📭 No hay usuarios en el sistema.\n")
                return
            
            print("\n" + "="*50)
            print("👥 USUARIOS EN EL SISTEMA")
            print("="*50 + "\n")
            
            for user in users:
                print(f"📧 {user.email}")
                print(f"   👤 Username: {user.username}")
                if user.full_name:
                    print(f"   📝 Nombre: {user.full_name}")
                print(f"   🔑 ID: {user.id}")
                print(f"   👑 Admin: {'Sí' if user.is_superuser else 'No'}")
                print(f"   ✅ Activo: {'Sí' if user.is_active else 'No'}")
                print()
            
    except Exception as e:
        print(f"\n❌ Error al listar usuarios: {str(e)}")
        logger.error(f"Error listing users: {e}")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_users()
    else:
        create_admin_user()


if __name__ == "__main__":
    main()
