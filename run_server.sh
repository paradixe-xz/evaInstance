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

# Usa watchmedo para reiniciar el servidor si hay cambios en .py o requirements.txt
watchmedo auto-restart --patterns="*.py;requirements.txt" --recursive -- \
  uvicorn main:app --host 0.0.0.0 --port 4000 