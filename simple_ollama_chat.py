#!/usr/bin/env python3
"""
Simple Ollama Chat Server - No HTTP daemon, pure CLI
"""
import subprocess
import json
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def chat_with_ollama(model_name, message, system_prompt=None):
    """Chat with Ollama using direct CLI - no HTTP daemon"""
    try:
        # Build prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\nUser: {message}\nAssistant:"
        else:
            full_prompt = f"User: {message}\nAssistant:"
        
        # Try models in order of preference
        models_to_try = [
            model_name,
            f"{model_name}:latest",
            "llama3.2:3b",
            "llama3.2",
            "llama2"
        ]
        
        for model in models_to_try:
            try:
                print(f"Trying model: {model}")
                cmd = ["ollama", "run", model, full_prompt]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8'
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    response = result.stdout.strip()
                    print(f"✅ Success with model: {model}")
                    return {
                        "success": True,
                        "response": response,
                        "model_used": model
                    }
                else:
                    print(f"❌ Failed with model {model}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout with model: {model}")
                continue
            except Exception as e:
                print(f"💥 Error with model {model}: {e}")
                continue
        
        return {
            "success": False,
            "error": "All models failed",
            "models_tried": models_to_try
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Chat error: {str(e)}"
        }

@app.route('/chat', methods=['POST'])
def chat():
    """Simple chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        model = data.get('model', 'cristina_20251011_232419')
        system_prompt = data.get('system_prompt', 'Eres un asistente útil. Responde en español.')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        result = chat_with_ollama(model, message, system_prompt)
        
        if result["success"]:
            return jsonify({
                "message": result["response"],
                "model_used": result["model_used"],
                "success": True
            })
        else:
            return jsonify({
                "error": result["error"],
                "models_tried": result.get("models_tried", []),
                "success": False
            }), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """List available models using CLI"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])  # Model name
            
            return jsonify({
                "models": models,
                "success": True
            })
        else:
            return jsonify({
                "error": "Failed to list models",
                "success": False
            }), 500
            
    except Exception as e:
        return jsonify({"error": f"Error listing models: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok", "message": "Simple Ollama Chat Server"})

if __name__ == '__main__':
    print("🚀 Starting Simple Ollama Chat Server...")
    print("📋 Endpoints:")
    print("   POST /chat - Chat with models")
    print("   GET /models - List available models")
    print("   GET /health - Health check")
    print("\n📝 Example usage:")
    print('   curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d \'{"message":"Hola"}\'')
    print("\n🎯 Server running on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
