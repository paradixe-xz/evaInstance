#!/bin/bash

echo "🔄 Reiniciando servidor con lógica mejorada de WhatsApp..."

# Detener procesos existentes
echo "Deteniendo procesos existentes..."
pkill -f "python.*src/api/mainApi.py" || true
pkill -f "uvicorn.*src.api.mainApi:app" || true

# Esperar un momento
sleep 2

# Verificar que no hay procesos corriendo
if pgrep -f "src/api/mainApi.py" > /dev/null; then
    echo "❌ Aún hay procesos corriendo, forzando cierre..."
    pkill -9 -f "src/api/mainApi.py" || true
    sleep 1
fi

# Iniciar servidor
echo "🚀 Iniciando servidor..."
python src/api/mainApi.py &

# Esperar a que el servidor inicie
sleep 3

# Verificar que el servidor está corriendo
if pgrep -f "main.py" > /dev/null; then
    echo "✅ Servidor iniciado correctamente"
    echo "📱 Webhook de WhatsApp actualizado con lógica mejorada:"
    echo "   - Pregunta: '¿Puedo llamarte?'"
    echo "   - Si dice 'SÍ' → Llamada inmediata (1 minuto)"
    echo "   - Si dice 'NO' → Permite escoger hora"
    echo "   - Usa el nombre de la persona en la llamada"
    echo "   - Guion de 10 minutos para las llamadas"
    echo ""
    echo "🔍 Para ver logs: tail -f nohup.out"
    echo "📊 Para ver estado: ./show_status.sh"
else
    echo "❌ Error iniciando servidor"
    exit 1
fi 