#!/bin/bash

echo "🤖 Actualizando modelo ANA para sistema de llamadas telefónicas"
echo "=============================================================="

# Verificar que Ollama esté instalado
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama no está instalado"
    echo "   Instala Ollama desde: https://ollama.ai"
    exit 1
fi

# Verificar que el archivo de prompt existe
if [ ! -f "system_prompt_updated.txt" ]; then
    echo "❌ Error: No se encuentra system_prompt_updated.txt"
    exit 1
fi

echo "📖 Leyendo nuevo prompt del sistema..."
PROMPT=$(cat system_prompt_updated.txt)

echo "🔄 Eliminando modelo ANA anterior si existe..."
ollama rm ana 2>/dev/null

echo "🚀 Creando nuevo modelo ANA optimizado para llamadas telefónicas..."

# Crear el modelo con el nuevo prompt
ollama create ana --from llama2 --modelfile <<EOF
FROM llama2
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
SYSTEM $PROMPT
EOF

if [ $? -eq 0 ]; then
    echo "✅ Modelo ANA actualizado exitosamente"
    echo ""
    echo "🎯 Nuevas capacidades del modelo:"
    echo "   • Optimizado para conversaciones telefónicas directas"
    echo "   • Enfoque en identificación de interés"
    echo "   • Manejo mejorado de objeciones"
    echo "   • Preparación para cierre humano"
    echo "   • Recopilación de información clave"
    echo ""
    echo "📊 Para verificar el modelo:"
    echo "   ollama list"
    echo ""
    echo "🧪 Para probar el modelo:"
    echo "   ollama run ana 'Hola, soy Juan y necesito un préstamo'"
    echo ""
    echo "🎉 ¡Modelo ANA listo para el sistema de llamadas directas!"
else
    echo "❌ Error creando el modelo ANA"
    exit 1
fi 