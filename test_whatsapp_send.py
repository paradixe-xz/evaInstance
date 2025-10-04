#!/usr/bin/env python3
"""
Test script to verify WhatsApp API connection by sending a test message
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.whatsapp_service import WhatsAppService
from app.core.logging import get_logger

logger = get_logger(__name__)

def test_whatsapp_send():
    """Test sending a message via WhatsApp API"""
    try:
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService()
        
        # Your phone number (replace with your actual WhatsApp number)
        # Format: country code + number (without + or spaces)
        # Example: for +1 234 567 8900, use "12345678900"
        test_phone_number = input("Enter your WhatsApp number (format: country_code + number, e.g., 573001234567): ")
        
        if not test_phone_number:
            print("❌ No phone number provided")
            return
        
        # Send test message
        print(f"📱 Sending test message to {test_phone_number}...")
        
        response = whatsapp_service.send_text_message(
            to=test_phone_number,
            message="🤖 Test message from your WhatsApp AI Backend! If you receive this, the API connection is working correctly."
        )
        
        print("✅ Message sent successfully!")
        print(f"📋 Response: {response}")
        
        if 'messages' in response and response['messages']:
            message_id = response['messages'][0].get('id')
            print(f"📨 Message ID: {message_id}")
        
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        logger.error(f"Error in test_whatsapp_send: {str(e)}")

if __name__ == "__main__":
    print("🔧 WhatsApp API Connection Test")
    print("=" * 40)
    test_whatsapp_send()