#!/bin/bash

# Script para mostrar el estado rápidamente
# Uso: ./show_status.sh

if [ -f "status.txt" ]; then
    echo "📊 Estado actual del sistema evaInstance:"
    echo "=========================================="
    cat status.txt
else
    echo "❌ Archivo status.txt no encontrado"
    echo "💡 Ejecuta primero: python3 src/core/statusMonitor.py"
    echo "   O inicia el servidor completo: ./scripts/runServer.sh"
fi 