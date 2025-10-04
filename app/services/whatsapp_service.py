"""
WhatsApp Business API service for sending and receiving messages
"""

import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.config import get_settings, get_whatsapp_api_url
from ..core.logging import get_logger
from ..core.exceptions import WhatsAppAPIError, ValidationError

logger = get_logger(__name__)
settings = get_settings()


class WhatsAppService:
    """Service for WhatsApp Business API operations"""
    
    def __init__(self):
        self.base_url = get_whatsapp_api_url()
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self.verify_token = settings.whatsapp_verify_token
        
        # Request headers
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"WhatsApp service initialized with phone number ID: {self.phone_number_id}")
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription
        
        Args:
            mode: Verification mode
            token: Verification token
            challenge: Challenge string
            
        Returns:
            Challenge string if verification successful, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verification successful")
            return challenge
        
        logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
        return None
    
    def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send a text message
        
        Args:
            to: Recipient phone number
            message: Message text
            
        Returns:
            API response
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            logger.info(f"Sending text message to {to}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Message sent successfully: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send message to {to}: {str(e)}"
            logger.error(error_msg)
            raise WhatsAppAPIError(error_msg, error_code="SEND_MESSAGE_FAILED")
    
    def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "es",
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message
        
        Args:
            to: Recipient phone number
            template_name: Template name
            language_code: Language code (default: es)
            parameters: Template parameters
            
        Returns:
            API response
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        template_data = {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
        
        if parameters:
            template_data["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                }
            ]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_data
        }
        
        try:
            logger.info(f"Sending template message '{template_name}' to {to}")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Template message sent successfully: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send template message to {to}: {str(e)}"
            logger.error(error_msg)
            raise WhatsAppAPIError(error_msg, error_code="SEND_TEMPLATE_FAILED")
    
    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            API response
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            logger.info(f"Marking message {message_id} as read")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Message marked as read: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to mark message as read: {str(e)}"
            logger.error(error_msg)
            raise WhatsAppAPIError(error_msg, error_code="MARK_READ_FAILED")
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook message
        
        Args:
            webhook_data: Raw webhook data
            
        Returns:
            Parsed message data or None if not a message
        """
        try:
            entry = webhook_data.get("entry", [])
            if not entry:
                return None
            
            changes = entry[0].get("changes", [])
            if not changes:
                return None
            
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                # Check for status updates
                statuses = value.get("statuses", [])
                if statuses:
                    return self._parse_status_update(statuses[0])
                return None
            
            message = messages[0]
            contacts = value.get("contacts", [])
            contact = contacts[0] if contacts else {}
            
            parsed_message = {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "timestamp": datetime.fromtimestamp(int(message.get("timestamp", 0))),
                "type": message.get("type"),
                "contact": {
                    "name": contact.get("profile", {}).get("name", ""),
                    "wa_id": contact.get("wa_id", "")
                }
            }
            
            # Parse message content based on type
            message_type = message.get("type")
            if message_type == "text":
                parsed_message["text"] = message.get("text", {}).get("body", "")
            elif message_type == "image":
                parsed_message["image"] = message.get("image", {})
            elif message_type == "audio":
                parsed_message["audio"] = message.get("audio", {})
            elif message_type == "video":
                parsed_message["video"] = message.get("video", {})
            elif message_type == "document":
                parsed_message["document"] = message.get("document", {})
            elif message_type == "location":
                parsed_message["location"] = message.get("location", {})
            elif message_type == "contacts":
                parsed_message["contacts"] = message.get("contacts", [])
            
            logger.info(f"Parsed incoming message: {parsed_message}")
            return parsed_message
            
        except Exception as e:
            error_msg = f"Failed to parse webhook message: {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg, error_code="PARSE_MESSAGE_FAILED")
    
    def _parse_status_update(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Parse message status update"""
        return {
            "type": "status",
            "message_id": status.get("id"),
            "status": status.get("status"),
            "timestamp": datetime.fromtimestamp(int(status.get("timestamp", 0))),
            "recipient_id": status.get("recipient_id")
        }
    
    def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get media URL from media ID
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media URL or None if failed
        """
        url = f"{self.base_url}/{media_id}"
        
        try:
            logger.info(f"Getting media URL for {media_id}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            media_url = result.get("url")
            logger.info(f"Media URL retrieved: {media_url}")
            return media_url
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to get media URL: {str(e)}"
            logger.error(error_msg)
            return None
    
    def download_media(self, media_url: str, file_path: str) -> bool:
        """
        Download media file
        
        Args:
            media_url: Media URL
            file_path: Local file path to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading media from {media_url}")
            response = requests.get(media_url, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Media downloaded successfully to {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to download media: {str(e)}"
            logger.error(error_msg)
            return False
    
    def validate_phone_number(self, phone_number: str) -> str:
        """
        Validate and format phone number
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            Formatted phone number
        """
        # Remove all non-digit characters
        clean_number = "".join(filter(str.isdigit, phone_number))
        
        # Add country code if missing (assuming Mexico +52)
        if len(clean_number) == 10:
            clean_number = "52" + clean_number
        elif len(clean_number) == 12 and clean_number.startswith("52"):
            pass  # Already has country code
        else:
            raise ValidationError(f"Invalid phone number format: {phone_number}")
        
        return clean_number