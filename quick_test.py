#!/usr/bin/env python3
"""Quick test of the fixed backend"""
import requests

try:
    print("🧪 Testing fixed backend...")
    
    response = requests.post(
        "http://localhost:8000/api/v1/agents/ollama/1/chat/public",
        json={"message": "Hola, funciona ahora?"},
        timeout=60
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS!")
        print(f"🤖 Response: {result.get('ai_response', 'No ai_response field')}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"💥 Error: {e}")
