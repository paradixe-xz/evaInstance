#!/usr/bin/env python3
"""
Test the simple chat server
"""
import requests
import json

def test_chat():
    """Test chat functionality"""
    print("🧪 Testing Simple Ollama Chat Server...")
    
    # Test health
    try:
        response = requests.get("http://localhost:5000/health")
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test models list
    try:
        response = requests.get("http://localhost:5000/models")
        models_data = response.json()
        print(f"📋 Available models: {models_data.get('models', [])}")
    except Exception as e:
        print(f"❌ Models list failed: {e}")
    
    # Test chat
    try:
        chat_data = {
            "message": "Hola, como estas? Responde brevemente.",
            "model": "cristina_20251011_232419"
        }
        
        print(f"\n💬 Sending message: {chat_data['message']}")
        print(f"🎯 Using model: {chat_data['model']}")
        
        response = requests.post(
            "http://localhost:5000/chat",
            json=chat_data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat successful!")
            print(f"🤖 Model used: {result.get('model_used', 'unknown')}")
            print(f"💭 Response: {result.get('message', 'No response')}")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"📄 Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Chat error: {e}")

if __name__ == "__main__":
    test_chat()
