#!/bin/bash

echo "🚀 Reiniciando Sistema ANA - Llamadas Directas con Análisis de IA"
echo "================================================================"

# Detener procesos existentes
echo "🛑 Deteniendo procesos existentes..."
pkill -f "python main.py" 2>/dev/null
pkill -f "uvicorn main:app" 2>/dev/null
sleep 2

# Verificar que no hay procesos corriendo
if pgrep -f "python main.py" > /dev/null; then
    echo "❌ No se pudo detener el proceso anterior"
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando directorios del sistema..."
mkdir -p conversations
mkdir -p transcripts
mkdir -p analysis
mkdir -p audio

# Verificar variables de entorno críticas
echo "🔧 Verificando configuración..."
if [ -z "$TWILIO_ACCOUNT_SID" ]; then
    echo "⚠️  ADVERTENCIA: TWILIO_ACCOUNT_SID no está configurado"
fi

if [ -z "$TWILIO_AUTH_TOKEN" ]; then
    echo "⚠️  ADVERTENCIA: TWILIO_AUTH_TOKEN no está configurado"
fi

if [ -z "$TWILIO_PHONE_NUMBER" ]; then
    echo "⚠️  ADVERTENCIA: TWILIO_PHONE_NUMBER no está configurado"
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "⚠️  ADVERTENCIA: ELEVENLABS_API_KEY no está configurado"
fi

# Verificar que el modelo ANA existe
echo "🤖 Verificando modelo ANA..."
if ! ollama list | grep -q "ana"; then
    echo "⚠️  ADVERTENCIA: Modelo 'ana' no encontrado"
    echo "   Ejecuta: ollama create ana --from llama2"
fi

# Iniciar servidor
echo "🚀 Iniciando servidor..."
echo "   URL: http://localhost:8000"
echo "   Documentación: http://localhost:8000/docs"
echo ""
echo "📋 Endpoints principales:"
echo "   POST /sendNumbers - Subir contactos y hacer llamadas"
echo "   GET  /conversations/status - Estado de conversaciones"
echo "   GET  /analysis/ready_for_human - Listos para seguimiento"
echo "   POST /analysis/mark_closed - Marcar como cerrado"
echo ""
echo "🧪 Para probar el sistema:"
echo "   python test_call_system.py"
echo ""
echo "📖 Documentación completa: README_SISTEMA_LLAMADAS.md"
echo ""

# Ejecutar servidor en background
nohup python main.py > server.log 2>&1 &

# Esperar a que el servidor esté listo
echo "⏳ Esperando que el servidor esté listo..."
sleep 5

# Verificar que el servidor está corriendo
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Servidor iniciado correctamente"
    echo "📊 Logs del servidor: tail -f server.log"
    echo ""
    echo "🎯 Sistema ANA - Llamadas Directas está listo!"
    echo "   • Carga contactos con archivo Excel"
    echo "   • Llamadas automáticas inmediatas"
    echo "   • Transcripción completa"
    echo "   • Análisis automático con IA"
    echo "   • Seguimiento humano inteligente"
else
    echo "❌ Error: El servidor no responde"
    echo "📋 Revisa los logs: cat server.log"
    exit 1
fi

echo ""
echo "🔄 Sistema reiniciado exitosamente!" 