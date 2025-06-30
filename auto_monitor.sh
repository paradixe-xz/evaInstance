#!/bin/bash

# Auto Monitor para evaInstance
# Actualiza el estado cada 30 segundos automáticamente

echo "🚀 Iniciando Auto Monitor para evaInstance..."
echo "📊 El estado se actualizará cada 30 segundos"
echo "📁 Archivo de estado: status.txt"
echo "⏹️  Presiona Ctrl+C para detener"
echo ""

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "🛑 Auto Monitor detenido"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Bucle principal
while true; do
    # Generar reporte
    python3 status_monitor.py > /dev/null 2>&1
    
    # Mostrar timestamp
    echo "✅ Estado actualizado: $(date '+%H:%M:%S')"
    
    # Esperar 30 segundos
    sleep 30
done 