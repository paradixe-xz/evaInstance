#!/bin/bash

# Script de configuración e inicio del backend de Eva AI Assistant
# Uso: bash setup-and-run.sh

set -e  # Detener en caso de error

echo "🚀 Eva AI Assistant - Setup y Ejecución del Backend"
echo "======================================================"

# Cambiar al directorio del script
cd "$(dirname "$0")"

# 1. Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "✅ Entorno virtual ya existe"
fi

# 2. Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# 3. Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# 4. Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# 5. Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado"
    if [ -f ".env.example" ]; then
        echo "📋 Copiando .env.example a .env..."
        cp .env.example .env
        echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales antes de continuar"
        echo "Press Enter para continuar después de editar .env..."
        read
    else
        echo "❌ No se encontró .env.example"
        exit 1
    fi
else
    echo "✅ Archivo .env encontrado"
fi

# 6. Inicializar base de datos (si es necesario)
if [ ! -f "whatsapp_ai.db" ]; then
    echo "🗄️  Inicializando base de datos..."
    python init_db.py
    echo "✅ Base de datos inicializada"
else
    echo "✅ Base de datos ya existe"
fi

# 7. Iniciar el servidor
echo ""
echo "======================================================"
echo "🎉 Iniciando servidor en http://localhost:8000"
echo "======================================================"
echo ""
python start.py
