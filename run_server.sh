#!/bin/bash

echo "🚀 Sistema ANA - Llamadas Directas con Análisis de IA"
echo "====================================================="

# Instala dependencias del sistema (ajusta según tu distro)
echo "📦 Instalando dependencias del sistema..."
apt update
apt install -y python3 python3-pip python3-venv

# Instala ffmpeg si no está instalado
echo "🎵 Verificando instalación de ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
  echo "ffmpeg no está instalado. Instalando..."
  apt-get install -y ffmpeg
else
  echo "ffmpeg ya está instalado."
fi

# Instala dependencias del sistema para TTS
echo "🎤 Instalando dependencias para TTS..."
apt-get install -y espeak espeak-data
apt-get install -y portaudio19-dev python3-pyaudio

# Crea entorno virtual si no existe
if [ ! -d "venv" ]; then
  echo "🐍 Creando entorno virtual..."
  python3 -m venv venv
fi

# Activa entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instala/actualiza dependencias
echo "📚 Instalando dependencias Python..."
pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install uvicorn watchdog python-dotenv

# Crear directorios necesarios para el nuevo sistema
echo "📁 Creando directorios del sistema..."
mkdir -p conversations
mkdir -p transcripts
mkdir -p analysis
mkdir -p audio

# Exporta variables de entorno desde .env si existe
if [ -f ".env" ]; then
  echo "⚙️ Cargando variables de entorno desde .env..."
  export $(grep -v '^#' .env | xargs)
fi

# Verificar variables de entorno críticas
echo "🔧 Verificando configuración..."
MISSING_VARS=()

if [ -z "$TWILIO_ACCOUNT_SID" ]; then
  echo "⚠️  ADVERTENCIA: TWILIO_ACCOUNT_SID no está configurado"
  MISSING_VARS+=("TWILIO_ACCOUNT_SID")
fi

if [ -z "$TWILIO_AUTH_TOKEN" ]; then
  echo "⚠️  ADVERTENCIA: TWILIO_AUTH_TOKEN no está configurado"
  MISSING_VARS+=("TWILIO_AUTH_TOKEN")
fi

if [ -z "$TWILIO_PHONE_NUMBER" ]; then
  echo "⚠️  ADVERTENCIA: TWILIO_PHONE_NUMBER no está configurado"
  MISSING_VARS+=("TWILIO_PHONE_NUMBER")
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
  echo "⚠️  ADVERTENCIA: ELEVENLABS_API_KEY no está configurado"
  MISSING_VARS+=("ELEVENLABS_API_KEY")
fi

# Verificar y actualizar el modelo ANA
echo "🤖 Verificando y actualizando modelo ANA..."
if [ -f "update_ana_phone_system.sh" ]; then
  echo "🔄 Actualizando modelo ANA para llamadas telefónicas..."
  chmod +x update_ana_phone_system.sh
  ./update_ana_phone_system.sh
  if [ $? -eq 0 ]; then
    echo "✅ Modelo ANA actualizado exitosamente"
  else
    echo "⚠️  Error actualizando modelo ANA, intentando crear básico..."
    ollama create ana --from llama2
  fi
else
  echo "⚠️  Script de actualización no encontrado, creando modelo básico..."
  ollama create ana --from llama2
fi

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo todos los procesos..."
    kill $SERVER_PID $MONITOR_PID 2>/dev/null
    echo "✅ Procesos detenidos"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

echo ""
echo "🎯 Sistema ANA - Llamadas Directas está configurado!"
echo "=================================================="
echo "📋 Funcionalidades:"
echo "   • Carga contactos con archivo Excel"
echo "   • Llamadas automáticas inmediatas"
echo "   • Transcripción completa de conversaciones"
echo "   • Análisis automático con IA"
echo "   • Seguimiento humano inteligente"
echo ""
echo "🌐 Servidor disponible en: http://localhost:4000"
echo "📚 Documentación: https://9jtwxh1smksq25-4000.proxy.runpod.net/docs"
echo "📊 Estado: cat status.txt"
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
echo "⏹️  Presiona Ctrl+C para detener todo"
echo ""

# Iniciar monitor de estado en segundo plano
echo "📊 Iniciando monitor de estado..."
python3 status_monitor.py > /dev/null 2>&1

# Función para el monitor que se ejecuta cada 30 segundos
monitor_loop() {
    while true; do
        python3 status_monitor.py > /dev/null 2>&1
        sleep 30
    done
}

# Iniciar monitor en segundo plano
monitor_loop &
MONITOR_PID=$!

echo "✅ Monitor iniciado (PID: $MONITOR_PID)"

# Iniciar servidor principal
echo "🌐 Iniciando servidor principal..."
uvicorn main:app --host 0.0.0.0 --port 4000 &
SERVER_PID=$!

echo "✅ Servidor iniciado (PID: $SERVER_PID)"
echo ""

# Mostrar información de configuración
if [ ${#MISSING_VARS[@]} -gt 0 ]; then
  echo "⚠️  VARIABLES FALTANTES:"
  for var in "${MISSING_VARS[@]}"; do
    echo "   - $var"
  done
  echo ""
  echo "💡 Configura estas variables en tu archivo .env o en el entorno"
  echo "   Ejemplo: export $var=tu_valor"
  echo ""
fi

echo "🎉 Sistema ANA completamente operativo!"
echo "   • Llamadas directas automáticas"
echo "   • Transcripción completa"
echo "   • Análisis inteligente de IA"
echo "   • Seguimiento humano optimizado"
echo ""

# Esperar a que termine cualquiera de los procesos
wait 