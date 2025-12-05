#!/bin/bash
# Script para iniciar el servicio systemd de Eva Backend

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Obtener la ruta absoluta del directorio actual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$SCRIPT_DIR"
VENV_PATH="$BACKEND_DIR/venv"

echo -e "${GREEN}🚀 Configurando servicio systemd para Eva Backend${NC}"

# Verificar que existe el entorno virtual
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ No se encontró el entorno virtual en: $VENV_PATH${NC}"
    echo -e "${YELLOW}💡 Crea el entorno virtual primero con: python3 -m venv venv${NC}"
    exit 1
fi

# Verificar que existe uvicorn
if [ ! -f "$VENV_PATH/bin/uvicorn" ]; then
    echo -e "${RED}❌ uvicorn no encontrado en el entorno virtual${NC}"
    echo -e "${YELLOW}💡 Instala las dependencias con: $VENV_PATH/bin/pip install -r requirements.txt${NC}"
    exit 1
fi

# Crear el archivo de servicio temporal con las rutas correctas
SERVICE_FILE="/tmp/eva-backend.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Eva AI Assistant Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_PATH/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=eva-backend

# Cargar variables de entorno desde .env si existe
EnvironmentFile=$BACKEND_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Archivo de servicio creado${NC}"
echo -e "${YELLOW}📋 Contenido del servicio:${NC}"
cat "$SERVICE_FILE"

echo ""
echo -e "${YELLOW}⚠️  Para instalar el servicio, ejecuta:${NC}"
echo -e "${GREEN}sudo cp $SERVICE_FILE /etc/systemd/system/eva-backend.service${NC}"
echo -e "${GREEN}sudo systemctl daemon-reload${NC}"
echo -e "${GREEN}sudo systemctl enable eva-backend${NC}"
echo -e "${GREEN}sudo systemctl start eva-backend${NC}"
echo ""
echo -e "${YELLOW}📝 Comandos útiles:${NC}"
echo -e "  Ver estado:     ${GREEN}sudo systemctl status eva-backend${NC}"
echo -e "  Ver logs:       ${GREEN}sudo journalctl -u eva-backend -f${NC}"
echo -e "  Reiniciar:      ${GREEN}sudo systemctl restart eva-backend${NC}"
echo -e "  Detener:        ${GREEN}sudo systemctl stop eva-backend${NC}"
echo -e "  Deshabilitar:   ${GREEN}sudo systemctl disable eva-backend${NC}"

