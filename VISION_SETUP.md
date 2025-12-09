# MiniCPM-V Vision Model Setup

## Paso 1: Instalar el modelo

En tu servidor donde corre Ollama, ejecuta:

```bash
ollama pull minicpm-v:8b
```

Esto descargará el modelo MiniCPM-V de 8B parámetros (~5GB).

## Paso 2: Configurar el .env

Agrega o modifica en tu archivo `.env`:

```bash
# Modelo de Ollama (cambiar a minicpm-v para visión)
OLLAMA_MODEL=minicpm-v:8b
```

## Paso 3: Reiniciar el backend

```bash
# Detener el backend actual (Ctrl+C)
# Luego reiniciar
python start.py
```

## ¿Qué hace MiniCPM-V?

- ✅ **Procesa imágenes directamente**: Ve el contenido visual de las imágenes
- ✅ **Lee PDFs con imágenes**: Puede "ver" PDFs escaneados o con gráficos
- ✅ **OCR automático**: Extrae texto de imágenes sin necesidad de pypdf
- ✅ **Multilingüe**: Soporta 30+ idiomas
- ✅ **Eficiente**: Optimizado para velocidad y memoria

## Alternativas si minicpm-v no funciona:

### Opción 2: llama3.2-vision
```bash
ollama pull llama3.2-vision:11b
OLLAMA_MODEL=llama3.2-vision:11b
```

### Opción 3: llava (más ligero)
```bash
ollama pull llava:13b
OLLAMA_MODEL=llava:13b
```

## Verificar que funciona:

Después de configurar, envía una imagen por WhatsApp y la IA debería poder describirla o responder preguntas sobre ella.
