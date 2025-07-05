#!/usr/bin/env python3
"""
Monitor de Estado en Tiempo Real para evaInstance
Genera un archivo de estado que se puede revisar con 'cat status.txt'
"""

import os
import json
import time
import pytz
from datetime import datetime, timedelta
import subprocess
import psutil
from pathlib import Path

# Configuración
TIMEZONE = pytz.timezone('America/Bogota')
CONVERSATIONS_DIR = "conversations"
AUDIO_DIR = "audio"
STATUS_FILE = "status.txt"
LOG_DIR = "logs"

def get_current_time():
    """Obtiene la hora actual en Barranquilla"""
    return datetime.now(TIMEZONE)

def format_duration(seconds):
    """Formatea duración en formato legible"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def get_system_info():
    """Obtiene información del sistema"""
    try:
        # CPU y memoria
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Procesos de Python
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Ordenar por uso de CPU
        python_processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': f"{memory.available / (1024**3):.1f} GB",
            'python_processes': python_processes[:5]  # Top 5 procesos
        }
    except Exception as e:
        return {'error': str(e)}

def get_conversations_status():
    """Obtiene el estado de todas las conversaciones"""
    conversations = []
    current_time = get_current_time()
    
    if not os.path.exists(CONVERSATIONS_DIR):
        return []
    
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.startswith("conversation-") and filename.endswith(".json"):
            number = filename.replace("conversation-", "").replace(".json", "")
            
            try:
                with open(os.path.join(CONVERSATIONS_DIR, filename), 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # Calcular tiempo desde última interacción
                last_interaction = datetime.fromisoformat(state.get("last_interaction", current_time.isoformat()))
                if last_interaction.tzinfo is None:
                    last_interaction = TIMEZONE.localize(last_interaction)
                
                time_diff = current_time - last_interaction
                
                # Estado de la llamada programada
                call_status = "No programada"
                if state.get("call_scheduled") and state.get("scheduled_time"):
                    scheduled_time = datetime.fromisoformat(state["scheduled_time"])
                    if scheduled_time.tzinfo is None:
                        scheduled_time = TIMEZONE.localize(scheduled_time)
                    
                    if scheduled_time > current_time:
                        time_until_call = scheduled_time - current_time
                        call_status = f"Programada para {scheduled_time.strftime('%H:%M')} (en {format_duration(time_until_call.total_seconds())})"
                    else:
                        call_status = "Vencida"
                
                conversations.append({
                    "number": number,
                    "name": state.get("name", "Sin nombre"),
                    "stage": state.get("stage", "unknown"),
                    "messages_sent": state.get("messages_sent", 0),
                    "call_scheduled": state.get("call_scheduled", False),
                    "call_status": call_status,
                    "last_interaction": state.get("last_interaction"),
                    "time_since_last_interaction": format_duration(time_diff.total_seconds()) if time_diff.total_seconds() > 0 else "Ahora mismo"
                })
            except Exception as e:
                conversations.append({
                    "number": number,
                    "name": "Error",
                    "stage": "error",
                    "error": str(e)
                })
    
    # Ordenar por última interacción (más reciente primero)
    conversations.sort(key=lambda x: x.get("last_interaction", ""), reverse=True)
    return conversations

def get_audio_files_info():
    """Obtiene información sobre archivos de audio"""
    if not os.path.exists(AUDIO_DIR):
        return {"count": 0, "total_size": "0 MB", "files": []}
    
    files = []
    total_size = 0
    
    for filename in os.listdir(AUDIO_DIR):
        if filename.endswith('.wav'):
            file_path = os.path.join(AUDIO_DIR, filename)
            try:
                size = os.path.getsize(file_path)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if modified_time.tzinfo is None:
                    modified_time = TIMEZONE.localize(modified_time)
                
                files.append({
                    "name": filename,
                    "size": f"{size / (1024*1024):.1f} MB",
                    "modified": modified_time.strftime('%H:%M:%S'),
                    "age": format_duration((get_current_time() - modified_time).total_seconds())
                })
                total_size += size
            except Exception:
                continue
    
    # Ordenar por fecha de modificación (más reciente primero)
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {
        "count": len(files),
        "total_size": f"{total_size / (1024*1024):.1f} MB",
        "files": files[:10]  # Solo los 10 más recientes
    }

def get_log_files_info():
    """Obtiene información sobre archivos de log"""
    log_files = []
    
    # Buscar archivos de chatlog
    for filename in os.listdir("."):
        if filename.startswith("chatlog-") and filename.endswith(".txt"):
            try:
                size = os.path.getsize(filename)
                modified_time = datetime.fromtimestamp(os.path.getmtime(filename))
                if modified_time.tzinfo is None:
                    modified_time = TIMEZONE.localize(modified_time)
                
                # Contar líneas
                with open(filename, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                
                log_files.append({
                    "name": filename,
                    "size": f"{size / 1024:.1f} KB",
                    "lines": line_count,
                    "modified": modified_time.strftime('%H:%M:%S'),
                    "age": format_duration((get_current_time() - modified_time).total_seconds())
                })
            except Exception:
                continue
    
    # Ordenar por fecha de modificación
    log_files.sort(key=lambda x: x["modified"], reverse=True)
    return log_files

def get_scheduler_jobs():
    """Obtiene información sobre trabajos programados"""
    try:
        # Intentar obtener trabajos del scheduler (si está corriendo)
        import requests
        response = requests.get("http://localhost:8000/conversations/status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("total_conversations", 0)
    except:
        pass
    
    # Si no se puede conectar, contar archivos de conversación programadas
    scheduled_count = 0
    if os.path.exists(CONVERSATIONS_DIR):
        for filename in os.listdir(CONVERSATIONS_DIR):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(CONVERSATIONS_DIR, filename), 'r') as f:
                        state = json.load(f)
                    if state.get("call_scheduled"):
                        scheduled_count += 1
                except:
                    continue
    
    return scheduled_count

def generate_status_report():
    """Genera el reporte completo de estado"""
    current_time = get_current_time()
    
    # Obtener información del sistema
    system_info = get_system_info()
    
    # Obtener conversaciones
    conversations = get_conversations_status()
    
    # Obtener información de audio
    audio_info = get_audio_files_info()
    
    # Obtener archivos de log
    log_files = get_log_files_info()
    
    # Contar llamadas programadas
    scheduled_calls = get_scheduler_jobs()
    
    # Generar reporte
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           EVA INSTANCE - ESTADO DEL SISTEMA                 ║
║                              {current_time.strftime('%d/%m/%Y %H:%M:%S')} - Barranquilla                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 INFORMACIÓN DEL SISTEMA
───────────────────────────────────────────────────────────────────────────────
• Hora actual: {current_time.strftime('%H:%M:%S')} (UTC-5)
• CPU: {system_info.get('cpu_percent', 'N/A')}%
• Memoria: {system_info.get('memory_percent', 'N/A')}% ({system_info.get('memory_available', 'N/A')} disponible)
• Llamadas programadas: {scheduled_calls}

💬 CONVERSACIONES ACTIVAS ({len(conversations)})
───────────────────────────────────────────────────────────────────────────────
"""
    
    if conversations:
        for i, conv in enumerate(conversations[:10], 1):  # Mostrar solo las 10 más recientes
            stage_emoji = {
                "initial": "🆕",
                "waiting_confirmation": "⏳",
                "scheduled_call": "📅",
                "call_in_progress": "📞",
                "completed": "✅",
                "error": "❌"
            }.get(conv["stage"], "❓")
            
            report += f"""
{i:2d}. {stage_emoji} {conv['name']} ({conv['number']})
    Estado: {conv['stage']} | Mensajes: {conv['messages_sent']} | Última interacción: {conv['time_since_last_interaction']}
    Llamada: {conv.get('call_status', 'No programada')}
"""
    else:
        report += "   No hay conversaciones activas\n"
    
    if len(conversations) > 10:
        report += f"   ... y {len(conversations) - 10} conversaciones más\n"
    
    report += f"""
🎵 ARCHIVOS DE AUDIO ({audio_info['count']})
───────────────────────────────────────────────────────────────────────────────
• Total: {audio_info['count']} archivos ({audio_info['total_size']})
"""
    
    if audio_info['files']:
        for file_info in audio_info['files'][:5]:  # Mostrar solo los 5 más recientes
            report += f"• {file_info['name']} ({file_info['size']}) - {file_info['age']} atrás\n"
    
    report += f"""
📝 ARCHIVOS DE LOG ({len(log_files)})
───────────────────────────────────────────────────────────────────────────────
"""
    
    if log_files:
        for log_file in log_files[:5]:  # Mostrar solo los 5 más recientes
            report += f"• {log_file['name']} ({log_file['size']}, {log_file['lines']} líneas) - {log_file['age']} atrás\n"
    
    report += f"""
🔧 PROCESOS PYTHON (Top 5 por CPU)
───────────────────────────────────────────────────────────────────────────────
"""
    
    for proc in system_info.get('python_processes', []):
        report += f"• PID {proc['pid']}: {proc['name']} - CPU: {proc['cpu_percent']}% | Mem: {proc['memory_percent']:.1f}%\n"
    
    report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              FIN DEL REPORTE                                ║
║                    Actualizado: {current_time.strftime('%H:%M:%S')}                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    return report

def main():
    """Función principal"""
    print("Generando reporte de estado...")
    
    try:
        report = generate_status_report()
        
        # Escribir al archivo
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Reporte generado en {STATUS_FILE}")
        print(f"📊 Para ver el estado: cat {STATUS_FILE}")
        
        # También mostrar en consola
        print("\n" + "="*80)
        print(report)
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")

if __name__ == "__main__":
    main() 