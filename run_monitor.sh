#!/bin/bash

# Script para ejecutar solo el monitor de estado
# Útil cuando el servidor ya está corriendo en otro proceso

echo "📊 Iniciando Monitor de Estado para evaInstance..."
echo "📁 Archivo de estado: status.txt"
echo "⏱️  Actualización cada 30 segundos"
echo "⏹️  Presiona Ctrl+C para detener"
echo ""

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "🛑 Monitor detenido"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Generar primer reporte
echo "🔄 Generando primer reporte..."
python3 status_monitor.py

echo "✅ Monitor iniciado. Para ver el estado: cat status.txt"
echo ""

# Bucle principal
while true; do
    # Generar reporte
    python3 status_monitor.py > /dev/null 2>&1
    
    # Mostrar timestamp
    echo "✅ Estado actualizado: $(date '+%H:%M:%S')"
    
    # Esperar 30 segundos
    sleep 30
done 