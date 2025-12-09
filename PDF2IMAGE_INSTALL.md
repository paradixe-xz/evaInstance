# Instalación de pdf2image

## Para Linux/Ubuntu (RunPod):
```bash
# Instalar poppler (requerido por pdf2image)
apt-get update
apt-get install -y poppler-utils

# Instalar pdf2image
pip install pdf2image
```

## Para Windows:
```bash
# Descargar poppler desde: https://github.com/oschwartz10612/poppler-windows/releases/
# Extraer y agregar a PATH

# Instalar pdf2image
pip install pdf2image
```

## Para macOS:
```bash
# Instalar poppler con Homebrew
brew install poppler

# Instalar pdf2image
pip install pdf2image
```

## Verificar instalación:
```python
from pdf2image import convert_from_path
print("✅ pdf2image instalado correctamente")
```
