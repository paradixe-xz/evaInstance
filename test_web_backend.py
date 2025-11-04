#!/usr/bin/env python3
"""
Test the main web backend with new CLI logic
"""
import requests
import json

def test_web_backend():
    """Test web backend functionality"""
    print("🧪 Testing Main Web Backend (port 8000)...")
    
    # Test health
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test ollama models endpoint
    try:
        response = requests.get("http://localhost:8000/api/v1/agents/ollama/base-models")
        if response.status_code == 200:
            models = response.json()
            print(f"📋 Ollama models endpoint: {len(models) if isinstance(models, list) else 'OK'}")
        else:
            print(f"📋 Ollama models endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Ollama models failed: {e}")
    
    # Test public chat (no auth needed)
    try:
        chat_data = {
            "message": "Hola, como estas? Responde brevemente en español."
        }
        
        print(f"\n💬 Testing public chat...")
        print(f"📝 Message: {chat_data['message']}")
        
        # Try agent ID 1 (common default)
        response = requests.post(
            "http://localhost:8000/api/v1/agents/ollama/1/chat/public",
            json=chat_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Public chat successful!")
            print(f"🤖 Response: {result.get('ai_response', 'No response')}")
        else:
            print(f"❌ Public chat failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Chat error: {e}")

    # Test creating a simple agent
    try:
        agent_data = {
            "name": "test-cli-agent",
            "description": "Test agent using CLI",
            "agent_type": "calls",
            "system_prompt": "Eres un asistente útil. Responde en español.",
            "is_ollama_model": True,
            "ollama_model_name": "cristina_20251011_232419",
            "base_model": "llama3.2:3b",
            "temperature": 0.7,
            "num_ctx": 4096
        }
        
        print(f"\n🔧 Testing agent creation...")
        response = requests.post(
            "http://localhost:8000/api/v1/agents/",
            json=agent_data,
            timeout=30
        )
        
        if response.status_code == 201:
            agent = response.json()
            agent_id = agent.get('id')
            print(f"✅ Agent created successfully! ID: {agent_id}")
            
            # Test chat with new agent
            if agent_id:
                chat_response = requests.post(
                    f"http://localhost:8000/api/v1/agents/ollama/{agent_id}/chat/public",
                    json={"message": "Hola, funciona el chat?"},
                    timeout=120
                )
                
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    print(f"✅ New agent chat works!")
                    print(f"🤖 Response: {chat_result.get('ai_response', 'No response')}")
                else:
                    print(f"❌ New agent chat failed: {chat_response.status_code}")
        else:
            print(f"❌ Agent creation failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Agent creation error: {e}")

if __name__ == "__main__":
    test_web_backend()
