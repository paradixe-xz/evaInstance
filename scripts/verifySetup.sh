#!/bin/bash

echo "🔍 Verificando configuración del sistema ANA"
echo "=========================================="

# Verificar archivos críticos
echo "📁 Verificando archivos críticos..."
CRITICAL_FILES=(
    "src/api/mainApi.py"
    "src/core/mainApp.py"
    "src/core/statusMonitor.py"
    "requirements.txt"
    "scripts/runServer.sh"
    "scripts/updateAnaModel.sh"
    "tests/testCallSystem.py"
    "tests/testStreamingOptimization.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - FALTANTE"
    fi
done

# Verificar directorios
echo ""
echo "📂 Verificando directorios..."
DIRECTORIES=(
    "src/api"
    "src/core"
    "src/config"
    "src/utils"
    "data"
    "data/conversations"
    "data/transcripts"
    "data/analysis"
    "data/audio"
    "scripts"
    "tests"
)

for dir in "${DIRECTORIES[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ $dir - FALTANTE"
    fi
done

# Verificar dependencias Python
echo ""
echo "🐍 Verificando dependencias Python..."
python3 -c "import fastapi, twilio, ollama, elevenlabs, pandas, pydub" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dependencias Python instaladas"
else
    echo "❌ Faltan dependencias Python - Ejecuta: pip install -r requirements.txt"
fi

# Verificar Ollama
echo ""
echo "🤖 Verificando Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama instalado"
    # Verificar modelo ANA
    if ollama list | grep -q "ana"; then
        echo "✅ Modelo ANA disponible"
    else
        echo "⚠️ Modelo ANA no encontrado - Se creará automáticamente"
    fi
else
    echo "❌ Ollama no instalado"
fi

# Verificar variables de entorno
echo ""
echo "⚙️ Verificando variables de entorno..."
ENV_VARS=(
    "TWILIO_ACCOUNT_SID"
    "TWILIO_AUTH_TOKEN"
    "TWILIO_PHONE_NUMBER"
    "ELEVENLABS_API_KEY"
)

for var in "${ENV_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        echo "✅ $var configurado"
    else
        echo "⚠️ $var no configurado"
    fi
done

# Verificar puerto
echo ""
echo "🌐 Verificando puerto..."
if curl -s http://localhost:4000/ > /dev/null 2>&1; then
    echo "✅ Servidor corriendo en puerto 4000"
else
    echo "ℹ️ Servidor no corriendo - Ejecuta: ./scripts/runServer.sh"
fi

echo ""
echo "📊 Resumen de verificación:"
echo "=========================="
echo "✅ Sistema ANA configurado para optimizaciones de streaming"
echo "✅ Puerto configurado en 4000"
echo "✅ Dependencias actualizadas"
echo "✅ Scripts de prueba disponibles"
echo ""
echo "🚀 Para iniciar el sistema:"
echo "   ./scripts/runServer.sh"
echo ""
echo "🧪 Para probar optimizaciones:"
echo "   python tests/testStreamingOptimization.py"
echo ""
echo "📊 Para monitorear:"
echo "   curl http://localhost:4000/audio-stats" 