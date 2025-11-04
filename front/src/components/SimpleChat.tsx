import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Trash2, Bug, CheckCircle, XCircle, UserPlus, Edit, ShoppingCart, CreditCard } from 'lucide-react';
import { apiClient } from '../services/api';
import { conversationAnalyzer, type ConversationContext } from '../services/conversationAnalyzer';
import { leadsApi, type LeadData } from '../services/leadsApi';
import { ordersApi, type OrderData } from '../services/ordersApi';
import { paymentsApi, type PaymentData } from '../services/paymentsApi';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export const SimpleChat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const [conversationContext, setConversationContext] = useState<ConversationContext | null>(null);
  const [leadCreated, setLeadCreated] = useState<string | null>(null);
  const [orderCreated, setOrderCreated] = useState<string | null>(null);
  const [paymentProcessed, setPaymentProcessed] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addLog = (log: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${log}`]);
  };

  // Analizar conversación después de cada mensaje
  useEffect(() => {
    if (messages.length > 0) {
      const context = conversationAnalyzer.analyzeConversation(messages);
      setConversationContext(context);
      
      addLog(`🧠 Análisis: ${context.detectedIntent} (${context.confidence.toFixed(1)}%)`);
      
      if (context.detectedIntent !== 'general_chat') {
        addLog(`📊 Datos extraídos: ${JSON.stringify(context.extractedData)}`);
        addLog(`❓ Campos faltantes: ${context.missingFields.join(', ') || 'ninguno'}`);
      }
      
      // Auto-crear lead si tenemos suficiente información
      if (conversationAnalyzer.shouldCreateLead(context)) {
        handleAutoCreateLead(context.extractedData as LeadData);
      }
      
      // Auto-actualizar lead si es necesario
      if (conversationAnalyzer.shouldUpdateLead(context)) {
        handleAutoUpdateLead(context.leadNumber!, context.extractedData);
      }
      
      // Auto-crear orden si tenemos suficiente información
      if (conversationAnalyzer.shouldCreateOrder(context)) {
        handleAutoCreateOrder(context.extractedOrderData as OrderData);
      }
      
      // Auto-procesar pago si tenemos suficiente información
      if (conversationAnalyzer.shouldProcessPayment(context)) {
        handleAutoProcessPayment(context.extractedPaymentData as PaymentData);
      }
    }
  }, [messages]);

  const handleAutoCreateLead = async (leadData: LeadData) => {
    try {
      addLog('🚀 Creando lead automáticamente...');
      const result = await leadsApi.createLead(leadData);
      
      if (result.rescode === '000' && result.leadnum) {
        setLeadCreated(result.leadnum);
        addLog(`✅ Lead creado: #${result.leadnum}`);
        
        // Agregar mensaje del sistema
        const systemMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: 'assistant',
          content: `🎉 ¡Perfecto! He creado tu lead con el número #${result.leadnum}. Tu información ha sido registrada exitosamente en nuestro sistema.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
      }
    } catch (error) {
      addLog(`❌ Error creando lead: ${error}`);
    }
  };

  const handleAutoUpdateLead = async (leadNumber: string, updateData: Partial<LeadData>) => {
    try {
      addLog(`🔄 Actualizando lead #${leadNumber}...`);
      const result = await leadsApi.updateLead(leadNumber, updateData);
      
      if (result.rescode === '000') {
        addLog(`✅ Lead #${leadNumber} actualizado`);
        
        // Agregar mensaje del sistema
        const systemMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: 'assistant',
          content: `✅ He actualizado la información del lead #${leadNumber} con los nuevos datos que me proporcionaste.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
      }
    } catch (error) {
      addLog(`❌ Error actualizando lead: ${error}`);
    }
  };

  const handleAutoCreateOrder = async (orderData: OrderData) => {
    try {
      addLog('🛒 Creando orden automáticamente...');
      const result = await ordersApi.createOrder(orderData);
      
      if (result.rescode === '000' && result.ordernum) {
        setOrderCreated(result.ordernum);
        addLog(`✅ Orden creada: #${result.ordernum}`);
        
        // Agregar mensaje del sistema
        const systemMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: 'assistant',
          content: `🛒 ¡Excelente! He creado tu orden con el número #${result.ordernum}. Tu pedido ha sido procesado exitosamente y será enviado en 7 días hábiles.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
      }
    } catch (error) {
      addLog(`❌ Error creando orden: ${error}`);
    }
  };

  const handleAutoProcessPayment = async (paymentData: PaymentData) => {
    try {
      addLog('💳 Procesando pago automáticamente...');
      
      // Validar datos de tarjeta antes de procesar
      if (!paymentsApi.validateCardNumber(paymentData.cardnumber)) {
        addLog('❌ Número de tarjeta inválido');
        return;
      }
      
      if (!paymentsApi.validateExpDate(paymentData.expdate)) {
        addLog('❌ Fecha de expiración inválida');
        return;
      }
      
      if (!paymentsApi.validateCVV(paymentData.cvv)) {
        addLog('❌ CVV inválido');
        return;
      }
      
      const result = await paymentsApi.processPayment(paymentData);
      
      if (result.rescode === '000' && result.receiptid) {
        setPaymentProcessed(result.receiptid);
        addLog(`✅ Pago procesado: Receipt #${result.receiptid}`);
        
        // Agregar mensaje del sistema
        const systemMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: 'assistant',
          content: `💳 ¡Pago procesado exitosamente! 
          
Detalles de la transacción:
• Receipt ID: #${result.receiptid}
• Authorization Code: ${result.authcode || 'N/A'}
• Transaction ID: ${result.transactionid || 'N/A'}
• Status: ${result.longmsg || 'APPROVED'}

Tu pago ha sido procesado y confirmado. Recibirás un email de confirmación en breve.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
      } else {
        addLog(`❌ Pago rechazado: ${result.longmsg || 'Error desconocido'}`);
        
        // Agregar mensaje de error
        const errorMessage: ChatMessage = {
          id: `system-${Date.now()}`,
          role: 'assistant',
          content: `❌ Lo siento, tu pago no pudo ser procesado. 

Motivo: ${result.longmsg || 'Error en el procesamiento'}
Código: ${result.rescode}

Por favor, verifica los datos de tu tarjeta e intenta nuevamente.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      addLog(`❌ Error procesando pago: ${error}`);
      
      // Agregar mensaje de error técnico
      const errorMessage: ChatMessage = {
        id: `system-${Date.now()}`,
        role: 'assistant',
        content: `❌ Error técnico al procesar el pago. Por favor, intenta más tarde o contacta a soporte técnico.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const testChat = async () => {
    if (!message.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setLoading(true);
    setError('');
    addLog(`Enviando mensaje: "${userMessage.content}"`);

    try {
      // Usar apiClient (que ya sabemos que funciona)
      addLog('Enviando con apiClient...');
      const apiResponse = await apiClient.chatWithOllamaModel(1, userMessage.content, []);
      addLog(`Respuesta: ${JSON.stringify(apiResponse)}`);

      if (apiResponse.error) {
        setError(apiResponse.error);
        addLog(`❌ Error: ${apiResponse.error}`);
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
        return;
      }

      if (apiResponse.data?.ai_response) {
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: apiResponse.data.ai_response,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, aiMessage]);
        addLog(`✅ Respuesta recibida correctamente`);
      } else {
        setError('No se recibió respuesta del modelo');
        addLog(`❌ No ai_response en respuesta`);
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
      }

    } catch (err: any) {
      const errorMsg = err.message || String(err);
      setError(`Error: ${errorMsg}`);
      addLog(`💥 Error: ${errorMsg}`);
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setLogs([]);
    setError('');
    setConversationContext(null);
    setLeadCreated(null);
    setOrderCreated(null);
    setPaymentProcessed(null);
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-800">Eva AI Test Chat</h1>
              <p className="text-sm text-gray-600">Probando conexión con el backend</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {conversationContext && conversationContext.detectedIntent !== 'general_chat' && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm">
                {conversationContext.detectedIntent === 'create_lead' && <UserPlus className="w-4 h-4" />}
                {conversationContext.detectedIntent === 'update_lead' && <Edit className="w-4 h-4" />}
                {conversationContext.detectedIntent === 'create_order' && <ShoppingCart className="w-4 h-4" />}
                {conversationContext.detectedIntent === 'process_payment' && <CreditCard className="w-4 h-4" />}
                <span>
                  {conversationContext.detectedIntent === 'create_lead' && 'Creando Lead'}
                  {conversationContext.detectedIntent === 'update_lead' && 'Actualizando Lead'}
                  {conversationContext.detectedIntent === 'create_order' && 'Creando Orden'}
                  {conversationContext.detectedIntent === 'process_payment' && 'Procesando Pago'}
                  {conversationContext.detectedIntent === 'gathering_info' && 'Recopilando Info'}
                </span>
                <span className="bg-green-200 px-2 py-0.5 rounded text-xs">
                  {conversationContext.confidence.toFixed(0)}%
                </span>
              </div>
            )}
            
            {leadCreated && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm">
                <CheckCircle className="w-4 h-4" />
                <span>Lead #{leadCreated}</span>
              </div>
            )}
            
            {orderCreated && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-purple-100 text-purple-700 rounded-lg text-sm">
                <ShoppingCart className="w-4 h-4" />
                <span>Orden #{orderCreated}</span>
              </div>
            )}
            
            {paymentProcessed && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm">
                <CreditCard className="w-4 h-4" />
                <span>Pago #{paymentProcessed}</span>
              </div>
            )}
            
            <button
              onClick={() => setShowLogs(!showLogs)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                showLogs 
                  ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Bug className="w-4 h-4 inline mr-1" />
              Debug
            </button>
            <button
              onClick={clearChat}
              className="px-3 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
            >
              <Trash2 className="w-4 h-4 inline mr-1" />
              Limpiar
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex max-w-4xl mx-auto w-full">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-white m-4 rounded-lg shadow-lg overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <Bot className="w-16 h-16 mb-4 text-gray-300" />
                <h3 className="text-lg font-medium mb-2">¡Comienza una conversación!</h3>
                <p className="text-sm text-center">Escribe un mensaje para probar la conexión con Eva AI</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-800 border border-gray-200'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {msg.role === 'assistant' && (
                        <Bot className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      )}
                      {msg.role === 'user' && (
                        <User className="w-5 h-5 text-white mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                        <span className={`text-xs mt-2 block ${
                          msg.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                        }`}>
                          {formatTimestamp(msg.timestamp)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 border border-gray-200 rounded-2xl px-4 py-3 max-w-[80%]">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-5 h-5 text-blue-600" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-sm text-gray-600">Pensando...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Error Message */}
          {error && (
            <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex space-x-3">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && testChat()}
                placeholder="Escribe tu mensaje..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                onClick={testChat}
                disabled={!message.trim() || loading}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
              >
                <Send className="w-5 h-5" />
                <span>{loading ? 'Enviando...' : 'Enviar'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Debug Panel */}
        {showLogs && (
          <div className="w-80 bg-white m-4 ml-0 rounded-lg shadow-lg overflow-hidden">
            <div className="bg-gray-800 text-white p-3 flex items-center space-x-2">
              <Bug className="w-5 h-5" />
              <h3 className="font-medium">Debug Logs</h3>
            </div>
            <div className="h-full overflow-y-auto p-3 bg-gray-900 text-green-400 font-mono text-xs">
              {logs.length === 0 ? (
                <p className="text-gray-500">No hay logs aún...</p>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="mb-1 break-words">
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SimpleChat;
