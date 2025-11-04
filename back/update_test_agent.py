#!/usr/bin/env python3
"""
Script para actualizar el modelo del agente de prueba
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db
from app.models.agent import Agent
from sqlalchemy.orm import Session

def update_test_agent():
    """Actualiza el modelo del agente de prueba"""
    
    # Inicializar la base de datos
    init_db()
    
    # Obtener sesión de base de datos
    db = next(get_db())
    
    try:
        # Buscar el agente de prueba
        agent = db.query(Agent).filter(Agent.name == "Test Chat Agent").first()
        
        if agent:
            # Actualizar el modelo a uno que existe
            agent.ollama_model_name = "llama3.2:3b"
            db.commit()
            print(f"✅ Agente actualizado: {agent.name} ahora usa el modelo {agent.ollama_model_name}")
        else:
            print("❌ No se encontró el agente de prueba")
            
    except Exception as e:
        print(f"❌ Error al actualizar el agente: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_test_agent()