import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ArrowLeft, Database, ToggleRight, ToggleLeft, Trash2, MessageCircle, BookOpen, Check, Copy } from 'lucide-react';
import { apiClient } from '../services/api';
import BrandLoader from './ui/BrandLoader';

interface KnowledgeSearchResult {
  chunk_id: number;
  content: string;
  similarity_score: number;
  document_filename: string;
  document_title?: string;
  page_number?: number;
  metadata?: Record<string, any>;
}

interface RAGResponse {
  response: string;
  sources: KnowledgeSearchResult[];
  search_query: string;
}
import { useAuth } from '../contexts/AuthContext';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: KnowledgeSearchResult[];
  knowledgeUsed?: boolean;
}

interface OllamaChatWithKnowledgeProps {
  agentId: number;
  agentName: string;
  modelName: string;
  onBack: () => void;
}

export const OllamaChatWithKnowledge: React.FC<OllamaChatWithKnowledgeProps> = ({ 
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
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(true);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
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

      let response;
      
      if (useKnowledgeBase) {
        // Use Knowledge Base enhanced chat
        response = await apiClient.chatWithKnowledge(
          agentId,
          userMessage.content,
          conversationHistory
        );
      } else {
        // Use regular chat
        response = await apiClient.chatWithOllamaModel(
          agentId,
          userMessage.content,
          conversationHistory
        );
      }

      if (response.error) {
        setError(response.error);
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
        return;
      }

      if (response.data) {
        let aiContent: string;
        let sources: KnowledgeSearchResult[] | undefined;
        let knowledgeUsed: boolean | undefined;

        if (useKnowledgeBase && 'sources' in response.data) {
          // RAG response
          const ragData = response.data as RAGResponse;
          aiContent = ragData.response;
          sources = ragData.sources;
          knowledgeUsed = sources && sources.length > 0;
        } else {
          // Regular response
          aiContent = response.data.response || '';
        }

        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: aiContent,
          timestamp: new Date(),
          sources,
          knowledgeUsed
        };

        setMessages(prev => [...prev, aiMessage]);
      } else {
        setError('No se recibió respuesta del servidor');
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
      }
    } catch (err: any) {
      console.error('Error sending message:', err);
      
      let errorMessage = 'Error al enviar el mensaje';
      
      if (err?.response?.data?.detail) {
        errorMessage = String(err.response.data.detail);
      } else if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }
      
      setError(errorMessage);
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
    if (confirm('¿Estás seguro de que quieres limpiar el chat?')) {
      setMessages([]);
      setError(null);
    }
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const toggleSourcesExpanded = (messageId: string) => {
    setExpandedSources(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Bot className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="font-semibold text-gray-900">{agentName}</h2>
              <p className="text-sm text-gray-500">{modelName}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Knowledge Base Toggle */}
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Knowledge Base</span>
            <button
              onClick={() => setUseKnowledgeBase(!useKnowledgeBase)}
              className={`p-1 rounded transition-colors ${
                useKnowledgeBase ? 'text-blue-600' : 'text-gray-400'
              }`}
              title={useKnowledgeBase ? 'Desactivar Knowledge Base' : 'Activar Knowledge Base'}
            >
              {useKnowledgeBase ? (
                <ToggleRight className="w-6 h-6" />
              ) : (
                <ToggleLeft className="w-6 h-6" />
              )}
            </button>
          </div>
          
          <button
            onClick={clearChat}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Limpiar chat"
          >
            <Trash2 className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Knowledge Base Status */}
      {useKnowledgeBase && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2">
          <div className="flex items-center gap-2 text-sm text-blue-700">
            <Database className="w-4 h-4" />
            <span>Knowledge Base activado - Las respuestas incluirán información de los documentos</span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-4">
          <div className="flex items-center gap-2 text-red-700">
            <MessageCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <Bot className="mx-auto w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">
              ¡Hola! Soy {agentName}
            </h3>
            <p className="text-gray-500 mb-4">
              {useKnowledgeBase 
                ? 'Puedo ayudarte usando la información de los documentos cargados.'
                : 'Estoy aquí para ayudarte. ¿En qué puedo asistirte?'
              }
            </p>
            {useKnowledgeBase && (
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                <Database className="w-4 h-4" />
                Knowledge Base activado
              </div>
            )}
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              </div>
            )}

            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Knowledge Base Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-gray-200">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <BookOpen className="w-4 h-4" />
                          <span>Fuentes ({message.sources.length})</span>
                          {message.knowledgeUsed && (
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                              Knowledge Base usado
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => toggleSourcesExpanded(message.id)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {expandedSources[message.id] ? 'Ocultar' : 'Ver fuentes'}
                        </button>
                      </div>
                      
                      {expandedSources[message.id] && (
                        <div className="space-y-2">
                          {message.sources.map((source, index) => (
                            <div
                              key={`${source.chunk_id}-${index}`}
                              className="bg-gray-50 rounded p-3 text-sm"
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium text-gray-700">
                                  {source.document_title || source.document_filename}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {(source.similarity_score * 100).toFixed(1)}% relevancia
                                </span>
                              </div>
                              <p className="text-gray-600 text-xs line-clamp-2">
                                {source.content.substring(0, 150)}...
                              </p>
                              {source.page_number && (
                                <span className="text-xs text-gray-500">
                                  Página {source.page_number}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1 ml-2">
                  <span className={`text-xs ${
                    message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                  }`}>
                    {formatTimestamp(message.timestamp)}
                  </span>
                  <button
                    onClick={() => copyToClipboard(message.content, message.id)}
                    className={`p-1 rounded hover:bg-opacity-20 hover:bg-gray-500 ${
                      message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
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

            {message.role === 'user' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <BrandLoader size="sm" label={useKnowledgeBase ? 'Buscando en la base de conocimiento...' : 'Pensando...'} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={useKnowledgeBase 
                ? "Pregunta algo sobre los documentos o cualquier tema..." 
                : "Escribe tu mensaje..."
              }
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <BrandLoader size="sm" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OllamaChatWithKnowledge;