"""
Conversation flow configurations for different AI personalities
"""

# Default conversation flow for EMA - Simplified: direct to AI conversation
DEFAULT_ISA_FLOW = {
    "initial_greeting": {
        "message": None,  # Let the AI model handle the greeting
        "next_step": "ai_conversation"
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
    "ema": DEFAULT_ISA_FLOW,
    "emma": DEFAULT_ISA_FLOW,  # Keep for backward compatibility
    "isa": DEFAULT_ISA_FLOW,  # Keep for backward compatibility
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
