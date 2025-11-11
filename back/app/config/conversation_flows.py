"""
Conversation flow configurations for different AI personalities
"""

# Default conversation flow for ISA
DEFAULT_ISA_FLOW = {
    "initial_greeting": {
        "message": "¡Hola! Soy ISA, tu asesora experta de Seguros Mundial. 😊 Gracias por contactarnos.\n\nAntes de continuar, necesito tu autorización para el manejo de datos personales. ¿Me autorizas a usar tu información únicamente para ofrecerte los mejores seguros y asesoría personalizada?\n\n📌 Recuerda: Tu información está protegida bajo la normativa de protección de datos.\n\nPor favor responde con 'sí' para continuar o 'no' si no deseas continuar.",
        "next_step": "waiting_authorization"
    },
    "waiting_authorization": {
        "message": "Gracias por tu respuesta. Para continuar con la conversación, necesito que confirmes tu autorización respondiendo 'sí'.",
        "next_step": {
            "sí": "ai_conversation",
            "si": "ai_conversation",
            "s": "ai_conversation"
        }
    },
    "ai_conversation": {
        "message": None,
        "next_step": "ai_conversation"
    },
    "home_insurance_flow": {
        "message": "¡Excelente elección! El Seguro de Hogar 'Vive Tranqui' te brinda protección completa para tu hogar. Para ofrecerte la mejor cotización, necesito algunos datos:",
        "questions": [
            {
                "question": "¿En qué ciudad se encuentra la propiedad a asegurar?",
                "field": "city"
            },
            {
                "question": "¿Cuál es el valor aproximado de los contenidos de tu hogar?",
                "field": "content_value"
            },
            {
                "question": "¿La propiedad es casa o apartamento?",
                "field": "property_type"
            }
        ],
        "next_step": "quote_generation"
    },
    "quote_generation": {
        "message": "¡Perfecto! Con los datos proporcionados, he generado una cotización personalizada. ¿Te gustaría que te envíe los detalles por correo electrónico?",
        "next_step": "email_confirmation"
    },
    "email_confirmation": {
        "message": "Por favor, confirma tu correo electrónico para enviarte la cotización.",
        "field": "email",
        "validation": "email",
        "next_step": "closing"
    },
    "closing": {
        "message": "¡Gracias por tu interés! Un asesor se pondrá en contacto contigo a la brevedad para finalizar el proceso. ¿Hay algo más en lo que pueda ayudarte?",
        "next_step": "end_conversation"
    },
    "end_conversation": {
        "message": "Ha sido un placer atenderte. ¡Que tengas un excelente día! 😊",
        "end": True
    }
}

# Add more flows as needed
CONVERSATION_FLOWS = {
    "isa": DEFAULT_ISA_FLOW,
    # Add other flows here
}

def get_flow(flow_name: str) -> dict:
    """
    Get conversation flow by name
    
    Args:
        flow_name: Name of the flow to retrieve
        
    Returns:
        dict: The requested conversation flow
    """
    return CONVERSATION_FLOWS.get(flow_name, DEFAULT_ISA_FLOW)
