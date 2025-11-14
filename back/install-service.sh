#!/bin/bash
# Script para instalar el servicio systemd de Eva Backend

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Por favor ejecuta este script con sudo${NC}"
    echo -e "${YELLOW}💡 Ejecuta: sudo ./install-service.sh${NC}"
    exit 1
fi

# Obtener la ruta absoluta del directorio actual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"
VENV_PATH="$BACKEND_DIR/venv"
SERVICE_NAME="eva-backend"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Instalador de Servicio Systemd - Eva Backend${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

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

# Obtener el usuario que ejecutó el script (antes de sudo)
REAL_USER=${SUDO_USER:-$USER}

echo -e "${YELLOW}📋 Configuración detectada:${NC}"
echo -e "   Directorio: ${GREEN}$BACKEND_DIR${NC}"
echo -e "   Entorno virtual: ${GREEN}$VENV_PATH${NC}"
echo -e "   Usuario: ${GREEN}$REAL_USER${NC}"
echo ""

# Crear el archivo de servicio
echo -e "${YELLOW}📝 Creando archivo de servicio...${NC}"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Eva AI Assistant Backend Service
After=network.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
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

# Configuración de seguridad
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Archivo de servicio creado en: $SERVICE_FILE${NC}"
echo ""

# Recargar systemd
echo -e "${YELLOW}🔄 Recargando systemd...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✅ systemd recargado${NC}"
echo ""

# Habilitar el servicio para que inicie automáticamente
echo -e "${YELLOW}🔧 Habilitando servicio para inicio automático...${NC}"
systemctl enable "$SERVICE_NAME"
echo -e "${GREEN}✅ Servicio habilitado${NC}"
echo ""

# Iniciar el servicio
echo -e "${YELLOW}🚀 Iniciando servicio...${NC}"
systemctl start "$SERVICE_NAME"
sleep 2

# Verificar el estado
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Servicio iniciado correctamente${NC}"
else
    echo -e "${RED}❌ Error al iniciar el servicio${NC}"
    echo -e "${YELLOW}💡 Revisa los logs con: sudo journalctl -u $SERVICE_NAME -n 50${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Instalación completada exitosamente${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📝 Comandos útiles:${NC}"
echo -e "  Ver estado:     ${GREEN}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "  Ver logs:       ${GREEN}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  Ver últimas:    ${GREEN}sudo journalctl -u $SERVICE_NAME -n 50${NC}"
echo -e "  Reiniciar:      ${GREEN}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Detener:        ${GREEN}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  Deshabilitar:   ${GREEN}sudo systemctl disable $SERVICE_NAME${NC}"
echo ""
echo -e "${YELLOW}💡 El servicio se iniciará automáticamente al reiniciar el sistema${NC}"
echo ""

