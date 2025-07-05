#!/bin/bash

echo "🧹 Limpiando archivos temporales y de prueba..."

# Eliminar archivos de audio temporales
echo "🗑️ Eliminando archivos de audio temporales..."
find . -name "temp_*.wav" -delete 2>/dev/null
find . -name "temp_*.mp3" -delete 2>/dev/null
find . -name "temp_speak.wav" -delete 2>/dev/null

# Eliminar archivos de log temporales
echo "🗑️ Eliminando archivos de log temporales..."
find . -name "chatlog-*.txt" -delete 2>/dev/null
find . -name "*.log" -delete 2>/dev/null

# Eliminar archivos de estado temporales
echo "🗑️ Eliminando archivos de estado temporales..."
rm -f status.txt 2>/dev/null
rm -f nohup.out 2>/dev/null

# Limpiar directorios de datos (mantener estructura)
echo "🗑️ Limpiando directorios de datos..."
rm -rf data/conversations/* 2>/dev/null
rm -rf data/transcripts/* 2>/dev/null
rm -rf data/analysis/* 2>/dev/null
rm -rf data/audio/* 2>/dev/null

# Crear archivos .gitkeep para mantener estructura
touch data/conversations/.gitkeep
touch data/transcripts/.gitkeep
touch data/analysis/.gitkeep
touch data/audio/.gitkeep

echo "✅ Limpieza completada"
echo "📁 Estructura de directorios mantenida" 