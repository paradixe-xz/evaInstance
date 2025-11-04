import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  MessageCircle,
  ArrowLeft,
  Trash2,
  Copy,
  Check
} from 'lucide-react';
import BrandLoader from './ui/BrandLoader';
import { apiClient } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface OllamaChatProps {
  agentId: number;
  agentName: string;
  modelName: string;
  onBack: () => void;
}

export const OllamaChat: React.FC<OllamaChatProps> = ({ 
  agentId, 
  agentName, 
  modelName, 
  onBack 
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      // Prepare conversation history for API
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      console.log('💬 Sending chat request:', {
        agentId,
        message: userMessage.content,
        conversationHistory
      });

      const response = await apiClient.chatWithOllamaModel(
        agentId,
        userMessage.content,
        conversationHistory
      );

      console.log('📨 Received response:', response);

      if (response.error) {
        // Manejar error de la API
        setError(response.error);
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
        return;
      }

      // El backend devuelve la respuesta en response.data.ai_response (confirmado por test)
      let aiResponseContent = '';
      
      console.log('🔍 Analizando respuesta completa:', response);
      
      if (response.data?.ai_response) {
        aiResponseContent = response.data.ai_response;
        console.log('✅ Encontrado ai_response:', aiResponseContent);
      } else {
        console.log('❌ No se encontró ai_response en:', response.data);
        console.log('🔍 Campos disponibles:', Object.keys(response.data || {}));
      }

      if (aiResponseContent && aiResponseContent.trim()) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: aiResponseContent.trim(),
          timestamp: new Date()
        };

        setMessages(prev => [...prev, aiMessage]);
      } else {
        console.error('No AI response found in:', response);
        setError('No se recibió respuesta válida del servidor');
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
        return;
      }
    } catch (err: any) {
      console.error('Error sending message:', err);
      console.error('Error type:', typeof err);
      console.error('Error keys:', Object.keys(err || {}));
      
      let errorMessage = 'Error al enviar el mensaje';
      
      try {
        // Verificar si es un error de la API
        if (err?.response?.data?.detail) {
          errorMessage = String(err.response.data.detail);
        } else if (err?.response?.data?.message) {
          errorMessage = String(err.response.data.message);
        } else if (err?.message && typeof err.message === 'string') {
          errorMessage = err.message;
        } else if (typeof err === 'string') {
          errorMessage = err;
        } else if (err?.error && typeof err.error === 'string') {
          errorMessage = err.error;
        } else if (err?.detail && typeof err.detail === 'string') {
          errorMessage = err.detail;
        } else if (err?.name === 'TypeError' || err?.name === 'NetworkError') {
          errorMessage = 'Error de conexión. Verifica que el servidor esté funcionando.';
        } else if (err instanceof Error) {
          errorMessage = err.message || 'Error desconocido';
        } else {
          // Si es un objeto, intentar extraer información útil
          if (typeof err === 'object' && err !== null) {
            const errorKeys = Object.keys(err);
            if (errorKeys.length > 0) {
              errorMessage = `Error: ${errorKeys.map(key => `${key}: ${err[key]}`).join(', ')}`;
            } else {
              errorMessage = 'Error desconocido en la comunicación con el servidor';
            }
          } else {
            errorMessage = 'Error desconocido al procesar la respuesta';
          }
        }
      } catch (stringifyError) {
        console.error('Error converting error to string:', stringifyError);
        errorMessage = 'Error desconocido al procesar la respuesta';
      }
      
      setError(errorMessage);
      
      // Remove the user message if there was an error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  const copyMessage = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center space-x-2">
            <Bot className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-800">{agentName}</h2>
              <p className="text-sm text-gray-600">{modelName}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={clearChat}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Limpiar chat"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <MessageCircle className="w-12 h-12 mb-4 text-gray-300" />
            <p className="text-lg font-medium">¡Comienza una conversación!</p>
            <p className="text-sm">Escribe un mensaje para probar tu modelo Ollama</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800 border border-gray-200'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.role === 'assistant' && (
                    <Bot className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  )}
                  {message.role === 'user' && (
                    <User className="w-5 h-5 text-white mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className={`text-xs ${
                        message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                      }`}>
                        {formatTimestamp(message.timestamp)}
                      </span>
                      <button
                        onClick={() => copyMessage(message.content, message.id)}
                        className={`p-1 rounded transition-colors ${
                          message.role === 'user'
                            ? 'hover:bg-blue-700 text-blue-200 hover:text-white'
                            : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'
                        }`}
                        title="Copiar mensaje"
                      >
                        {copiedMessageId === message.id ? (
                          <Check className="w-3 h-3" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 border border-gray-200 rounded-lg p-3 max-w-[80%]">
              <div className="flex items-center space-x-2">
                <Bot className="w-5 h-5 text-blue-600" />
                <div className="flex items-center">
                  <BrandLoader size="sm" label="Pensando..." />
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <div className="flex space-x-3">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isLoading ? (
              <BrandLoader size="sm" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OllamaChat;