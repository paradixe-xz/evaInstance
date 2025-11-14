# 🚀 Instalación del Servicio Systemd para Eva Backend

Este documento explica cómo instalar el backend de Eva como un servicio systemd en Linux, para que se ejecute automáticamente al iniciar el sistema y se reinicie si se cae.

## 📋 Requisitos Previos

1. Sistema operativo Linux con systemd
2. Python 3.8+ instalado
3. Entorno virtual creado y dependencias instaladas
4. Permisos de administrador (sudo)

## 🔧 Instalación Rápida

### Opción 1: Script Automático (Recomendado)

```bash
cd back
chmod +x install-service.sh
sudo ./install-service.sh
```

El script automáticamente:
- Detecta las rutas correctas
- Crea el archivo de servicio
- Lo instala en systemd
- Habilita el inicio automático
- Inicia el servicio

### Opción 2: Instalación Manual

1. **Crear el archivo de servicio:**

```bash
sudo nano /etc/systemd/system/eva-backend.service
```

2. **Copiar el siguiente contenido** (ajusta las rutas según tu instalación):

```ini
[Unit]
Description=Eva AI Assistant Backend Service
After=network.target

[Service]
Type=simple
User=tu_usuario
Group=tu_usuario
WorkingDirectory=/ruta/completa/a/evaInstance/back
Environment="PATH=/ruta/completa/a/evaInstance/back/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/ruta/completa/a/evaInstance/back/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=eva-backend

# Cargar variables de entorno desde .env
EnvironmentFile=/ruta/completa/a/evaInstance/back/.env

[Install]
WantedBy=multi-user.target
```

3. **Recargar systemd y habilitar el servicio:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable eva-backend
sudo systemctl start eva-backend
```

## 📊 Comandos Útiles

### Ver el estado del servicio
```bash
sudo systemctl status eva-backend
```

### Ver los logs en tiempo real
```bash
sudo journalctl -u eva-backend -f
```

### Ver las últimas 50 líneas de logs
```bash
sudo journalctl -u eva-backend -n 50
```

### Reiniciar el servicio
```bash
sudo systemctl restart eva-backend
```

### Detener el servicio
```bash
sudo systemctl stop eva-backend
```

### Iniciar el servicio
```bash
sudo systemctl start eva-backend
```

### Deshabilitar el inicio automático
```bash
sudo systemctl disable eva-backend
```

### Habilitar el inicio automático
```bash
sudo systemctl enable eva-backend
```

## 🔄 Actualizar el Servicio

Cuando actualices el código del backend, el servicio se reiniciará automáticamente si se cae. Para forzar un reinicio después de cambios:

```bash
sudo systemctl restart eva-backend
```

## 🐛 Solución de Problemas

### El servicio no inicia

1. **Verifica los logs:**
```bash
sudo journalctl -u eva-backend -n 100
```

2. **Verifica que las rutas sean correctas:**
```bash
sudo systemctl status eva-backend
```

3. **Verifica que el entorno virtual existe:**
```bash
ls -la /ruta/a/evaInstance/back/venv/bin/python
```

4. **Verifica que uvicorn está instalado:**
```bash
/ruta/a/evaInstance/back/venv/bin/uvicorn --version
```

### El servicio se reinicia constantemente

1. **Revisa los logs para ver el error:**
```bash
sudo journalctl -u eva-backend -n 100 --no-pager
```

2. **Verifica el archivo .env:**
```bash
cat /ruta/a/evaInstance/back/.env
```

3. **Prueba ejecutar manualmente:**
```bash
cd /ruta/a/evaInstance/back
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### El servicio no se inicia al arrancar el sistema

1. **Verifica que esté habilitado:**
```bash
sudo systemctl is-enabled eva-backend
```

2. **Habilítalo si no lo está:**
```bash
sudo systemctl enable eva-backend
```

## 📝 Notas Importantes

- El servicio se ejecuta como el usuario que ejecutó el script de instalación
- Los logs se guardan en el journal de systemd
- El servicio se reinicia automáticamente si se cae (después de 10 segundos)
- El servicio inicia automáticamente al arrancar el sistema
- El servicio sigue activo aunque cierres la terminal

## 🔒 Seguridad

- El servicio se ejecuta con el usuario especificado (no como root, a menos que sea necesario)
- Las variables de entorno se cargan desde el archivo `.env`
- Los logs están disponibles solo para usuarios con permisos de administrador

## 📞 Soporte

Si tienes problemas, revisa los logs primero:
```bash
sudo journalctl -u eva-backend -f
```

