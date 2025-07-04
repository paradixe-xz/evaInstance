#!/bin/bash

echo "🔄 Reiniciando Sistema ANA con saludo pre-generado..."
echo "=================================================="

# Detener procesos existentes
echo "🛑 Deteniendo procesos existentes..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*status_monitor.py" 2>/dev/null
sleep 2

# Limpiar archivos de audio temporales
echo "🧹 Limpiando archivos temporales..."
rm -f audio/*.temp.* 2>/dev/null

# Verificar que los cambios están aplicados
echo "✅ Verificando cambios aplicados..."
if grep -q "Generando saludo personalizado para" main.py; then
    echo "✅ Función schedule_call actualizada"
else
    echo "❌ Error: Cambios no aplicados en schedule_call"
    exit 1
fi

if grep -q "Usando saludo pre-generado" main.py; then
    echo "✅ Endpoint twilio/voice actualizado"
else
    echo "❌ Error: Cambios no aplicados en twilio/voice"
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p audio
mkdir -p conversations
mkdir -p transcripts
mkdir -p analysis

# Probar la generación de saludo
echo "🧪 Probando generación de saludo..."
python test_pre_generated_greeting.py

if [ $? -eq 0 ]; then
    echo "✅ Prueba de saludo exitosa"
else
    echo "⚠️ Advertencia: Prueba de saludo falló, pero continuando..."
fi

# Iniciar el servidor
echo "🚀 Iniciando servidor con saludo pre-generado..."
./run_server.sh

echo "🎉 Sistema ANA reiniciado con saludo pre-generado!"
echo "📋 Beneficios implementados:"
echo "   • Saludo se genera ANTES de la llamada"
echo "   • ANA habla inmediatamente al contestar"
echo "   • Sin demoras de generación de audio"
echo "   • Experiencia más fluida para el usuario" 