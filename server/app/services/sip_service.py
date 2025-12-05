"""
Servicio para manejo de conexiones SIP y SIP Trunks
"""
import logging
import asyncio
import socket
import hashlib
import secrets
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.sip_trunk import SIPTrunk
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SIPService:
    """Servicio para manejar conexiones SIP y troncos"""
    
    def __init__(self):
        self.active_trunks: Dict[int, Dict] = {}
        self.active_calls: Dict[str, Dict] = {}
        self.sip_server: Optional[asyncio.Server] = None
        self.is_running = False
        
    async def start_sip_server(self, host: str = "0.0.0.0", port: int = 5060):
        """Iniciar servidor SIP para recibir conexiones"""
        try:
            self.sip_server = await asyncio.start_server(
                self._handle_sip_connection,
                host,
                port
            )
            self.is_running = True
            logger.info(f"Servidor SIP iniciado en {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Error iniciando servidor SIP: {e}")
            return False
    
    async def stop_sip_server(self):
        """Detener servidor SIP"""
        if self.sip_server:
            self.sip_server.close()
            await self.sip_server.wait_closed()
            self.is_running = False
            logger.info("Servidor SIP detenido")
    
    async def _handle_sip_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Manejar conexión SIP entrante"""
        try:
            data = await reader.read(4096)
            message = data.decode('utf-8', errors='ignore')
            
            # Parsear mensaje SIP básico
            if message.startswith('REGISTER'):
                await self._handle_register(message, writer)
            elif message.startswith('INVITE'):
                await self._handle_invite(message, writer)
            elif message.startswith('ACK'):
                await self._handle_ack(message, writer)
            elif message.startswith('BYE'):
                await self._handle_bye(message, writer)
            else:
                await self._send_sip_response(writer, 400, "Bad Request")
                
        except Exception as e:
            logger.error(f"Error manejando conexión SIP: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _handle_register(self, message: str, writer: asyncio.StreamWriter):
        """Manejar registro SIP"""
        try:
            # Extraer información del mensaje REGISTER
            lines = message.split('\r\n')
            username = None
            domain = None
            
            for line in lines:
                if line.startswith('To:'):
                    # Extraer usuario y dominio de "To: <sip:user@domain>"
                    parts = line.split('<sip:')
                    if len(parts) > 1:
                        user_domain = parts[1].split('>')[0]
                        if '@' in user_domain:
                            username, domain = user_domain.split('@', 1)
            
            if not username or not domain:
                await self._send_sip_response(writer, 400, "Bad Request")
                return
            
            # Buscar tronco SIP en la base de datos
            db = SessionLocal()
            try:
                trunk = db.query(SIPTrunk).filter(
                    SIPTrunk.sip_username == username,
                    SIPTrunk.sip_domain == domain,
                    SIPTrunk.is_active == True
                ).first()
                
                if trunk:
                    # Verificar autenticación (simplificado - en producción usar digest auth)
                    trunk.is_registered = True
                    trunk.registration_status = "registered"
                    trunk.last_registration_at = datetime.utcnow()
                    db.commit()
                    
                    self.active_trunks[trunk.id] = {
                        'trunk': trunk,
                        'registered_at': datetime.utcnow(),
                        'writer': writer
                    }
                    
                    await self._send_sip_response(writer, 200, "OK")
                    logger.info(f"Tronco SIP registrado: {username}@{domain}")
                else:
                    await self._send_sip_response(writer, 403, "Forbidden")
                    logger.warning(f"Intento de registro no autorizado: {username}@{domain}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error en registro SIP: {e}")
            await self._send_sip_response(writer, 500, "Internal Server Error")
    
    async def _handle_invite(self, message: str, writer: asyncio.StreamWriter):
        """Manejar INVITE (llamada entrante)"""
        try:
            # Extraer información de la llamada
            call_id = self._extract_header(message, 'Call-ID')
            from_header = self._extract_header(message, 'From')
            to_header = self._extract_header(message, 'To')
            
            if not call_id:
                await self._send_sip_response(writer, 400, "Bad Request")
                return
            
            # Buscar tronco asociado
            trunk_id = self._find_trunk_by_connection(writer)
            
            if trunk_id:
                # Registrar llamada
                self.active_calls[call_id] = {
                    'call_id': call_id,
                    'trunk_id': trunk_id,
                    'from': from_header,
                    'to': to_header,
                    'started_at': datetime.utcnow(),
                    'status': 'ringing'
                }
                
                # Responder con 100 Trying
                await self._send_sip_response(writer, 100, "Trying")
                
                # Procesar llamada (aquí se integraría con el sistema de llamadas)
                logger.info(f"Llamada entrante SIP: {call_id} desde {from_header}")
                
                # Responder con 180 Ringing
                await self._send_sip_response(writer, 180, "Ringing")
                
                # Simular respuesta 200 OK (en producción, esto dependería del procesamiento)
                await self._send_sip_response(writer, 200, "OK")
            else:
                await self._send_sip_response(writer, 403, "Forbidden")
                
        except Exception as e:
            logger.error(f"Error manejando INVITE: {e}")
            await self._send_sip_response(writer, 500, "Internal Server Error")
    
    async def _handle_ack(self, message: str, writer: asyncio.StreamWriter):
        """Manejar ACK (confirmación de llamada establecida)"""
        call_id = self._extract_header(message, 'Call-ID')
        if call_id and call_id in self.active_calls:
            self.active_calls[call_id]['status'] = 'established'
            logger.info(f"Llamada establecida: {call_id}")
    
    async def _handle_bye(self, message: str, writer: asyncio.StreamWriter):
        """Manejar BYE (finalización de llamada)"""
        call_id = self._extract_header(message, 'Call-ID')
        if call_id and call_id in self.active_calls:
            call = self.active_calls[call_id]
            call['status'] = 'ended'
            call['ended_at'] = datetime.utcnow()
            
            # Calcular duración
            if 'started_at' in call:
                duration = (call['ended_at'] - call['started_at']).total_seconds()
                call['duration'] = duration
            
            await self._send_sip_response(writer, 200, "OK")
            logger.info(f"Llamada finalizada: {call_id}")
            
            # Limpiar llamada después de un tiempo
            del self.active_calls[call_id]
    
    def _extract_header(self, message: str, header: str) -> Optional[str]:
        """Extraer valor de un header SIP"""
        lines = message.split('\r\n')
        for line in lines:
            if line.startswith(f'{header}:'):
                return line.split(':', 1)[1].strip()
        return None
    
    def _find_trunk_by_connection(self, writer: asyncio.StreamWriter) -> Optional[int]:
        """Encontrar tronco por conexión"""
        for trunk_id, trunk_info in self.active_trunks.items():
            if trunk_info.get('writer') == writer:
                return trunk_id
        return None
    
    async def _send_sip_response(self, writer: asyncio.StreamWriter, code: int, reason: str):
        """Enviar respuesta SIP"""
        response = f"SIP/2.0 {code} {reason}\r\n"
        response += f"Via: SIP/2.0/UDP\r\n"
        response += f"Content-Length: 0\r\n\r\n"
        writer.write(response.encode())
        await writer.drain()
    
    def register_trunk(self, trunk: SIPTrunk) -> Tuple[bool, str]:
        """Registrar un tronco SIP manualmente"""
        try:
            db = SessionLocal()
            try:
                trunk.is_registered = True
                trunk.registration_status = "registered"
                trunk.last_registration_at = datetime.utcnow()
                db.commit()
                
                self.active_trunks[trunk.id] = {
                    'trunk': trunk,
                    'registered_at': datetime.utcnow()
                }
                
                logger.info(f"Tronco SIP registrado manualmente: {trunk.name}")
                return True, "Tronco registrado exitosamente"
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error registrando tronco: {e}")
            return False, str(e)
    
    def unregister_trunk(self, trunk_id: int) -> Tuple[bool, str]:
        """Desregistrar un tronco SIP"""
        try:
            db = SessionLocal()
            try:
                trunk = db.query(SIPTrunk).filter(SIPTrunk.id == trunk_id).first()
                if trunk:
                    trunk.is_registered = False
                    trunk.registration_status = "unregistered"
                    db.commit()
                    
                    if trunk_id in self.active_trunks:
                        del self.active_trunks[trunk_id]
                    
                    logger.info(f"Tronco SIP desregistrado: {trunk.name}")
                    return True, "Tronco desregistrado exitosamente"
                else:
                    return False, "Tronco no encontrado"
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error desregistrando tronco: {e}")
            return False, str(e)
    
    def get_trunk_status(self, trunk_id: int) -> Optional[Dict]:
        """Obtener estado de un tronco"""
        if trunk_id in self.active_trunks:
            trunk_info = self.active_trunks[trunk_id]
            trunk = trunk_info['trunk']
            return {
                'id': trunk.id,
                'name': trunk.name,
                'is_registered': trunk.is_registered,
                'registration_status': trunk.registration_status,
                'current_calls': trunk.current_calls,
                'max_concurrent_calls': trunk.max_concurrent_calls,
                'last_registration_at': trunk.last_registration_at.isoformat() if trunk.last_registration_at else None
            }
        return None
    
    def get_all_active_trunks(self) -> List[Dict]:
        """Obtener todos los troncos activos"""
        return [self.get_trunk_status(trunk_id) for trunk_id in self.active_trunks.keys()]


# Instancia global del servicio SIP
sip_service = SIPService()

