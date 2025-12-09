#!/usr/bin/env python3
"""
Script para crear usuarios administradores
Conecta con el backend API igual que la vista de registro

Uso: python create_admin.py
"""

import requests
import sys
from getpass import getpass

# URL del backend
API_URL = "http://localhost:8000/api/v1"


def create_admin_user():
    """Crear un nuevo usuario administrador"""
    print("\n" + "="*50)
    print("🔐 CREAR NUEVO USUARIO ADMINISTRADOR")
    print("="*50 + "\n")
    
    # Obtener datos del usuario
    email = input("📧 Email: ").strip()
    if not email:
        print("❌ Email es requerido")
        return
    
    name = input("📝 Nombre completo: ").strip()
    if not name:
        print("❌ Nombre es requerido")
        return
    
    company = input("🏢 Empresa (opcional): ").strip() or None
    
    # Obtener contraseña con confirmación
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
    
    # Preparar datos para el API
    user_data = {
        "email": email,
        "password": password,
        "name": name
    }
    
    if company:
        user_data["company"] = company
    
    # Enviar solicitud al backend
    try:
        print("\n⏳ Creando usuario...")
        response = requests.post(
            f"{API_URL}/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            user = response.json()
            print("\n" + "="*50)
            print("✅ USUARIO CREADO EXITOSAMENTE")
            print("="*50)
            print(f"\n📧 Email: {user.get('email')}")
            print(f"📝 Nombre: {user.get('name')}")
            if user.get('company'):
                print(f"🏢 Empresa: {user.get('company')}")
            print(f"🔑 ID: {user.get('id')}")
            print("\n✨ El usuario puede iniciar sesión ahora.\n")
        else:
            error_data = response.json()
            error_msg = error_data.get('detail', 'Error desconocido')
            print(f"\n❌ Error al crear usuario: {error_msg}\n")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ No se pudo conectar al backend en {API_URL}")
        print("   Asegúrate de que el servidor esté corriendo.\n")
    except requests.exceptions.Timeout:
        print("\n❌ Timeout al conectar con el backend\n")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")


def list_users():
    """Listar usuarios (requiere autenticación)"""
    print("\n⚠️  Para listar usuarios necesitas estar autenticado.")
    print("   Usa el dashboard web para ver los usuarios.\n")


def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_users()
    else:
        create_admin_user()


if __name__ == "__main__":
    main()
