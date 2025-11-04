#!/usr/bin/env python3
"""
Script para crear un agente de prueba en la base de datos
"""

import sqlite3
import os
from datetime import datetime

def create_test_agent():
    """Crea un agente de prueba en la base de datos"""
    
    db_path = "whatsapp_ai.db"
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si ya existe un usuario de prueba
        cursor.execute("SELECT id FROM system_users WHERE email = ?", ("test@example.com",))
        user = cursor.fetchone()
        
        if not user:
            # Crear usuario de prueba
            cursor.execute("""
                INSERT INTO system_users (email, hashed_password, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("test@example.com", "hashed_password", True, datetime.utcnow(), datetime.utcnow()))
            user_id = cursor.lastrowid
            print(f"✅ Usuario de prueba creado con ID: {user_id}")
        else:
            user_id = user[0]
            print(f"✅ Usuario de prueba encontrado con ID: {user_id}")
        
        # Eliminar agente existente si existe
        cursor.execute("DELETE FROM agents WHERE name = ?", ("Test Chat Agent",))
        
        # Crear agente de prueba con modelo correcto
        cursor.execute("""
            INSERT INTO agents (
                name, description, agent_type, status, is_active,
                model, temperature, max_tokens, system_prompt,
                is_ollama_model, ollama_model_name, base_model,
                personality_traits, conversation_style, response_time_limit,
                voice_id, voice_speed, voice_pitch,
                creator_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Test Chat Agent",
            "Agente de prueba para testing",
            "chat",
            "active",
            True,
            "llama3.2:3b",
            0.7,
            2000,
            "Eres un asistente útil y amigable. Responde de manera clara y concisa.",
            True,
            "llama3.2:3b",
            "llama3.2:3b",
            '["amigable","útil","profesional"]',
            "conversacional",
            30,
            "default",
            1.0,
            1.0,
            user_id,
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        agent_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Agente de prueba creado con ID: {agent_id}")
        print(f"   Modelo: llama3.2:3b")
        print(f"   Usuario: {user_id}")
        
    except Exception as e:
        print(f"❌ Error al crear el agente: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_test_agent()