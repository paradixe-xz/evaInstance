#!/bin/bash

echo "⚡ Probando optimizaciones de streaming de audio"
echo "=============================================="

# Verificar que el servidor esté corriendo
echo "🔍 Verificando servidor..."
if curl -s http://localhost:4000/ > /dev/null; then
    echo "✅ Servidor disponible"
else
    echo "❌ Servidor no disponible. Iniciando..."
    ./scripts/runServer.sh &
    sleep 5
fi

# Ejecutar pruebas de optimización
echo ""
echo "🧪 Ejecutando pruebas de optimización..."
python3 tests/testStreamingOptimization.py

echo ""
echo "📊 Verificando estadísticas de audio..."
curl -s http://localhost:4000/audio-stats | python3 -m json.tool

echo ""
echo "🧹 Ejecutando limpieza de audio..."
curl -s -X POST http://localhost:4000/cleanup-audio | python3 -m json.tool

echo ""
echo "✅ Pruebas completadas"
echo "💡 Para monitorear en tiempo real:"
echo "   curl http://localhost:4000/audio-stats"
echo "   tail -f nohup.out" 