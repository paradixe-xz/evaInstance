"""
WhatsApp Business API Integration
Mantiene la estructura actual del proyecto
"""

import os
import requests
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppBusinessAPI:
    """Clase para manejar WhatsApp Business API"""
    
    def __init__(self):
        # Variables de entorno para WhatsApp Business API
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        self.webhook_secret = os.getenv('WHATSAPP_WEBHOOK_SECRET')
        
        # URL base de la API
        self.base_url = "https://graph.facebook.com/v18.0"
        
        # Verificar configuración
        if not all([self.access_token, self.phone_number_id]):
            logger.warning("⚠️ WhatsApp Business API no configurado completamente")
            logger.info("Variables requeridas: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID")
    
    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Envía mensaje de texto usando WhatsApp Business API"""
        try:
            if not self.access_token or not self.phone_number_id:
                return {"error": "WhatsApp Business API no configurado"}
            
            # Limpiar número
            if not to_number.startswith('+'):
                to_number = '+' + to_number
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"✅ Mensaje WhatsApp enviado: {result.get('messages', [{}])[0].get('id')}")
                return {
                    "status": "success",
                    "message_id": result.get('messages', [{}])[0].get('id'),
                    "whatsapp_business_account_id": result.get('messaging_product')
                }
            else:
                logger.error(f"❌ Error enviando mensaje: {result}")
                return {"error": f"Error API: {result}"}
                
        except Exception as e:
            logger.error(f"Error en send_text_message: {e}")
            return {"error": str(e)}
    
    def send_template_message(self, to_number: str, template_name: str, language_code: str = "es", components: List[Dict] = None) -> Dict[str, Any]:
        """Envía mensaje de plantilla usando WhatsApp Business API"""
        try:
            if not self.access_token or not self.phone_number_id:
                return {"error": "WhatsApp Business API no configurado"}
            
            # Limpiar número
            if not to_number.startswith('+'):
                to_number = '+' + to_number
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            # Agregar componentes si se proporcionan
            if components:
                data["template"]["components"] = components
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"✅ Plantilla WhatsApp enviada: {result.get('messages', [{}])[0].get('id')}")
                return {
                    "status": "success",
                    "message_id": result.get('messages', [{}])[0].get('id'),
                    "template_name": template_name
                }
            else:
                logger.error(f"❌ Error enviando plantilla: {result}")
                return {"error": f"Error API: {result}"}
                
        except Exception as e:
            logger.error(f"Error en send_template_message: {e}")
            return {"error": str(e)}
    
    def send_media_message(self, to_number: str, media_url: str, media_type: str = "image", caption: str = None) -> Dict[str, Any]:
        """Envía mensaje con media usando WhatsApp Business API"""
        try:
            if not self.access_token or not self.phone_number_id:
                return {"error": "WhatsApp Business API no configurado"}
            
            # Limpiar número
            if not to_number.startswith('+'):
                to_number = '+' + to_number
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": media_type,
                media_type: {
                    "link": media_url
                }
            }
            
            # Agregar caption si se proporciona
            if caption:
                data[media_type]["caption"] = caption
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"✅ Media WhatsApp enviado: {result.get('messages', [{}])[0].get('id')}")
                return {
                    "status": "success",
                    "message_id": result.get('messages', [{}])[0].get('id'),
                    "media_type": media_type
                }
            else:
                logger.error(f"❌ Error enviando media: {result}")
                return {"error": f"Error API: {result}"}
                
        except Exception as e:
            logger.error(f"Error en send_media_message: {e}")
            return {"error": str(e)}
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verifica webhook de WhatsApp Business API"""
        try:
            if token == self.verify_token:
                logger.info("✅ Webhook verificado correctamente")
                return challenge
            else:
                logger.error("❌ Token de verificación incorrecto")
                return None
        except Exception as e:
            logger.error(f"Error verificando webhook: {e}")
            return None
    
    def process_webhook(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa webhook de WhatsApp Business API"""
        try:
            # Extraer datos del webhook
            entry = body.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Verificar que sea un mensaje
            if 'messages' not in value:
                return {"status": "no_message"}
            
            message = value['messages'][0]
            
            # Extraer información del mensaje
            message_data = {
                "from": message.get('from'),
                "timestamp": message.get('timestamp'),
                "type": message.get('type'),
                "message_id": message.get('id')
            }
            
            # Procesar según el tipo de mensaje
            if message.get('type') == 'text':
                message_data["text"] = message.get('text', {}).get('body', '')
            elif message.get('type') == 'interactive':
                # Manejar botones y listas
                interactive = message.get('interactive', {})
                message_data["interactive_type"] = interactive.get('type')
                if interactive.get('type') == 'button_reply':
                    message_data["button_text"] = interactive.get('button_reply', {}).get('title', '')
                elif interactive.get('type') == 'list_reply':
                    message_data["list_selection"] = interactive.get('list_reply', {}).get('title', '')
            
            logger.info(f"📱 Mensaje WhatsApp procesado: {message_data}")
            return message_data
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            return {"error": str(e)}
    
    def get_phone_number_info(self) -> Dict[str, Any]:
        """Obtiene información del número de WhatsApp Business"""
        try:
            if not self.access_token or not self.phone_number_id:
                return {"error": "WhatsApp Business API no configurado"}
            
            url = f"{self.base_url}/{self.phone_number_id}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "phone_number": result.get('phone_number'),
                    "display_phone_number": result.get('display_phone_number'),
                    "quality_rating": result.get('quality_rating'),
                    "verified_name": result.get('verified_name')
                }
            else:
                return {"error": f"Error API: {result}"}
                
        except Exception as e:
            logger.error(f"Error obteniendo info del número: {e}")
            return {"error": str(e)}
    
    def get_templates(self) -> Dict[str, Any]:
        """Obtiene plantillas disponibles"""
        try:
            if not self.access_token or not self.business_account_id:
                return {"error": "WhatsApp Business API no configurado"}
            
            url = f"{self.base_url}/{self.business_account_id}/message_templates"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "templates": result.get('data', [])
                }
            else:
                return {"error": f"Error API: {result}"}
                
        except Exception as e:
            logger.error(f"Error obteniendo plantillas: {e}")
            return {"error": str(e)}

# Instancia global
whatsapp_business = WhatsAppBusinessAPI() 