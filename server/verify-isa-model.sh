#!/bin/bash

# Script para verificar y crear el modelo ISA en Ollama
# Ejecutar en el contenedor Docker

set -e

echo "🔍 Verificando modelo ISA en Ollama..."

# Verificar si Ollama está corriendo
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama no está instalado"
    echo "Instalar con: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Verificar si el modelo ISA existe
if ollama list | grep -q "^isa"; then
    echo "✅ Modelo ISA ya existe"
    ollama list | grep "^isa"
else
    echo "⚠️  Modelo ISA no encontrado"
    
    # Verificar si existe el modelfileisa
    if [ -f "/evaInstance/modelfileisa" ]; then
        echo "📦 Creando modelo ISA desde modelfileisa..."
        cd /evaInstance
        ollama create isa -f modelfileisa
        
        if [ $? -eq 0 ]; then
            echo "✅ Modelo ISA creado exitosamente"
            ollama list | grep "^isa"
        else
            echo "❌ Error al crear el modelo ISA"
            exit 1
        fi
    else
        echo "❌ No se encontró el archivo modelfileisa"
        echo "Verifica que exista en /evaInstance/modelfileisa"
        exit 1
    fi
fi

echo ""
echo "🎉 Modelo ISA verificado correctamente"
echo ""
echo "Próximos pasos:"
echo "1. Reiniciar el backend: python3 start.py"
echo "2. Enviar mensaje de prueba por WhatsApp"
echo "3. Verificar logs que mencionen 'model: isa'"
