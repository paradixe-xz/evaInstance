#!/bin/bash

# Instala dependencias del sistema (ajusta según tu distro)
apt update
apt install -y python3 python3-pip python3-venv

# Instala ffmpeg si no está instalado
echo "Verificando instalación de ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
  echo "ffmpeg no está instalado. Instalando..."
  apt-get install -y ffmpeg
else
  echo "ffmpeg ya está instalado."
fi

# Instala dependencias del sistema para TTS
echo "Instalando dependencias para TTS..."
apt-get install -y espeak espeak-data
apt-get install -y portaudio19-dev python3-pyaudio

# Crea entorno virtual si no existe
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activa entorno virtual
source venv/bin/activate

# Instala/actualiza dependencias
pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install uvicorn watchdog python-dotenv

# Exporta variables de entorno desde .env si existe
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
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

echo "🚀 Iniciando evaInstance con monitor de estado..."
echo "📊 El estado se actualizará automáticamente en status.txt"
echo "🌐 Servidor disponible en: http://localhost:4000"
echo "📁 Para ver el estado: cat status.txt"
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

# Esperar a que termine cualquiera de los procesos
wait 