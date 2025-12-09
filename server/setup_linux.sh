#!/bin/bash

# setup_linux.sh - Script de instalación automatizada para Eva AI Assistant (Backend)
# Uso: ./setup_linux.sh

set -e

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Iniciando instalación de Eva AI Assistant Backend...${NC}"

# 0. Instalar dependencias del sistema (sudo, nano, git, python, pip)
echo -e "${YELLOW}📦 Verificando paquetes del sistema...${NC}"

if command -v apt-get &> /dev/null; then
    echo -e "🔄 Actualizando repositorios e instalando paquetes básicos..."
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        # Running as root: use apt-get directly
        echo -e "👤 Ejecutando como root: Instalando paquetes con apt-get..."
        apt-get update
        apt-get install -y sudo nano git python3 python3-pip python3-venv portaudio19-dev
    elif command -v sudo &> /dev/null; then
        # Not root, but sudo is available
        echo -e "🛡️  Usando sudo para instalar paquetes..."
        sudo apt-get update
        sudo apt-get install -y nano git python3 python3-pip python3-venv portaudio19-dev
    else
        # Not root, no sudo
        echo -e "${RED}⚠️  No tienes permisos de root ni está instalado 'sudo'. No se pueden instalar paquetes del sistema.${NC}"
        echo -e "Por favor contacta al administrador del sistema o instala los paquetes manualmente."
    fi
else
    echo -e "${YELLOW}⚠️  'apt-get' no encontrado. Asegúrate de tener instalados: sudo, nano, git, python3, pip.${NC}"
fi

# 1. Verificar Python (ahora debería estar sí o sí)
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no encontrado incluso después de intentar instalarlo.${NC}"
    exit 1
fi

echo -e "✅ Python 3 detectado: $(python3 --version)"

# 2. Crear entorno virtual (venv)
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creando entorno virtual (venv)...${NC}"
    python3 -m venv venv || { echo -e "${RED}❌ Falló la creación del venv. Asegúrate de tener python3-venv instalado.${NC}"; exit 1; }
    echo -e "✅ Entorno virtual creado"
else
    echo -e "⚠️  El entorno virtual ya existe"
fi

# 3. Activar entorno virtual
source venv/bin/activate
echo -e "✅ Entorno virtual activado"

# 4. Actualizar pip dentro del venv
echo -e "${YELLOW}⬇️  Actualizando pip interno...${NC}"
pip install --upgrade pip

# 5. Instalar requerimientos
echo -e "${YELLOW}⬇️  Instalando dependencias desde requirements.txt...${NC}"
# Estructura de instalación robusta
pip install wheel setuptools

# Intentar instalar todo
if pip install -r requirements.txt; then
    echo -e "${GREEN}✅ Dependencias instaladas correctamente${NC}"
else
    echo -e "${RED}⚠️  Hubo un error instalando algunas dependencias.${NC}"
    echo -e "${YELLOW}🔄 Intentando instalar dependencias core ignorando errores opcionales de audio...${NC}"
    
    # Instalación fail-safe
    pip install fastapi uvicorn python-multipart sqlalchemy requests httpx python-dotenv pydantic structlog ollama apscheduler psutil aiosip
    
    echo -e "${YELLOW}⚠️  Nota: El servidor funcionará, pero las funciones de voz (TTS/STT) pueden estar limitadas si falló la instalación de librerías de audio.${NC}"
fi

# 6. Configuración inicial
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Copiando .env.example a .env...${NC}"
    cp .env.example .env
    echo -e "✅ Archivo .env creado. ¡Recuerda editarlo con 'nano .env'!"
fi

# 7. Script de inicio
echo -e "${GREEN}🎉 Instalación completada.${NC}"
echo -e ""
echo -e "Para iniciar el servidor, ejecuta:"
echo -e "${YELLOW}./start.sh${NC}"
echo -e ""

# Crear script start.sh helper
cat > start.sh << EOL
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
python start.py
EOL
chmod +x start.sh
