#!/usr/bin/env python3
"""
Test the exact API call that frontend makes
"""
import requests
import json

def test_frontend_api_call():
    """Test the exact API call that frontend makes"""
    print("🧪 Testing Frontend API Call...")
    
    # Test the exact endpoint and payload that frontend uses
    try:
        # This is exactly what the frontend sends
        payload = {
            "message": "Hola, como estas? Responde brevemente.",
            "conversation_history": []
        }
        
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        print(f"🎯 Endpoint: POST /api/v1/agents/ollama/1/chat/public")
        
        response = requests.post(
            "http://localhost:8000/api/v1/agents/ollama/1/chat/public",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"📋 Full Response: {json.dumps(result, indent=2)}")
            
            # Check what frontend expects
            if 'ai_response' in result:
                print(f"🤖 AI Response: {result['ai_response']}")
                print(f"✅ Frontend should work - ai_response field present")
            else:
                print(f"❌ Frontend will show 'No response' - ai_response field missing")
                print(f"🔍 Available fields: {list(result.keys())}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Error text: {response.text}")
                
    except Exception as e:
        print(f"💥 Request error: {e}")

    # Test with different agent IDs to find a working one
    print(f"\n🔍 Testing different agent IDs...")
    for agent_id in [1, 2, 3]:
        try:
            response = requests.post(
                f"http://localhost:8000/api/v1/agents/ollama/{agent_id}/chat/public",
                json={"message": "Test"},
                timeout=30
            )
            print(f"Agent ID {agent_id}: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if 'ai_response' in result:
                    print(f"  ✅ Working agent found: {agent_id}")
                    print(f"  🤖 Response: {result['ai_response'][:50]}...")
                    break
        except Exception as e:
            print(f"Agent ID {agent_id}: Error - {e}")

if __name__ == "__main__":
    test_frontend_api_call()
