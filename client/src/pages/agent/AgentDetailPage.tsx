import { useState, useEffect, useRef } from 'react';
import { MediaRecorder, register } from 'extendable-media-recorder';
import { connect } from 'extendable-media-recorder-wav-encoder';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import { Bot, Save, MessageSquare, Settings, Loader2 } from 'lucide-react';
import { AgentLayout } from '../../components/layout/AgentLayout';
import api from '../../services/api';
import { API_BASE_URL } from '../../config/api';

const API_URL = API_BASE_URL;

type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  id?: number;
};

type AIAgent = {
  id: number;
  name: string;
  description: string;
  model: string;
  status: string;
  is_active: boolean;
  is_ollama_model: boolean;
  ollama_model_name: string | null;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  agent_type: string;
  created_at: string;
  updated_at: string;
  // Add other properties that might be present in the agent object
  base_model?: string;
  campaign_id?: number | null;
  creator_id?: number;
  avg_interaction_duration?: number;
  avg_response_time?: number;
  conversation_structure?: any;
  conversation_style?: string;
  custom_template?: any;
  feedback_score?: number;
  last_training_date?: string | null;
  last_used?: string | null;
  modelfile_content?: string | null;
  num_ctx?: number;
  ollama_parameters?: any;
  personality_traits?: any;
  response_time_limit?: number;
  success_rate?: number;
  successful_interactions?: number;
  total_cost?: number;
  total_interactions?: number;
  training_data?: any;
  voice_id?: string | null;
  voice_pitch?: number;
  voice_speed?: number;
  workflow_steps?: any;
};

export function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { logout: _ } = useAuth(); // Keep for potential future use
  const [agent, setAgent] = useState<AIAgent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<AIAgent>>({});
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [ttsAvailable, setTtsAvailable] = useState<boolean>(true);
  const [voiceMessages, setVoiceMessages] = useState<Message[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [tabValue, setTabValue] = useState<string>('chat');
  const [isRecording, setIsRecording] = useState(false);
  const [isVoiceProcessing, setIsVoiceProcessing] = useState(false);
  const [sttTranscript, setSttTranscript] = useState('');
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const mediaRecorderRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    const checkTts = async () => {
      try {
        const resp = await api.get(`${API_URL}/calls/tts/status`);
        setTtsAvailable(Boolean(resp.data?.available));
      } catch {
        setTtsAvailable(false);
      }
    };
    checkTts();

    // Register WAV encoder
    const initEncoder = async () => {
      try {
        await register(await connect());
      } catch (e) {
        // Ignore if already registered
        console.log('Encoder registration:', e);
      }
    };
    initEncoder();
  }, []);

  console.log('AgentDetailPage mounted with ID:', id);

  console.log('AgentDetailPage rendered with id:', id);

  useEffect(() => {
    const fetchAgent = async () => {
      if (!id) {
        setIsLoading(false);
        return;
      }

      try {
        console.log('Fetching agent with ID:', id);
        const response = await api.get(`${API_URL}/agents/${id}`);
        console.log('Agent data received:', response.data);

        if (response.data) {
          setAgent(response.data);
          setFormData(response.data);
        } else {
          console.error('No data received for agent');
          toast.error('No se encontró el agente');
        }
      } catch (error: any) {
        console.error('Error fetching agent:', error);
        const errorMessage = error.response?.data?.detail || 'No se pudo cargar el agente';
        toast.error(errorMessage);

        if (error.response?.status === 404) {
          // Redirect to agents list if agent not found
          navigate('/dashboard/agentes');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgent();
  }, [id, navigate]);

  const handleSave = async () => {
    if (!id) return;

    setIsSaving(true);
    setError(null);

    try {
      const response = await api.put(`${API_URL}/agents/${id}`, formData);
      setAgent(response.data);
      setFormData(response.data);
      setIsEditing(false);
      toast.success('Cambios guardados correctamente');
    } catch (error: any) {
      console.error('Error updating agent:', error);
      const errorMessage = error.response?.data?.detail || 'No se pudieron guardar los cambios';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    if (isSending) return;

    if (!id) {
      console.error('No agent ID found');
      toast.error('No se pudo identificar el agente');
      return;
    }

    // Check if agent is properly configured as an Ollama model
    if (!agent?.is_ollama_model) {
      console.error('Agent is not an Ollama model:', agent);
      toast.error('Este agente no está configurado como un modelo Ollama');
      return;
    }

    if (!agent.ollama_model_name) {
      console.error('Agent is missing Ollama model name:', agent);
      toast.error('Este agente no tiene un nombre de modelo Ollama asignado. Por favor, actualiza la configuración del agente.');
      return;
    }

    const userMessage = { role: 'user', content: message };
    const tempMessageId = Date.now();

    try {
      // Add the user message to the UI immediately
      setMessages(prev => [...prev, { ...userMessage, id: tempMessageId } as Message]);
      setMessage('');
      setIsSending(true);

      // Send message via query and conversation_history in body to match FastAPI signature
      const history = [...messages, userMessage].map(m => ({ role: m.role, content: m.content }));
      const requestData = { message: userMessage.content, conversation_history: history };
      const url = `${API_URL}/agents/ollama/${id}/chat/stream`;

      console.log('Sending message to agent:', {
        url,
        method: 'POST',
        data: requestData
      });

      try {
        // Streaming fetch with AbortController
        const controller = new AbortController();
        setAbortController(controller);
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` },
          body: JSON.stringify(requestData),
          signal: controller.signal,
        });
        if (!resp.ok || !resp.body) {
          throw new Error(`HTTP ${resp.status}`);
        }
        // Prepare assistant message placeholder
        const assistantId = Date.now() + 1;
        setMessages(prev => [
          ...prev.filter(msg => msg.id !== tempMessageId),
          userMessage,
          { role: 'assistant', content: '', id: assistantId } as Message
        ]);
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        const appendDelta = (delta: string) => {
          setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: (m.content || '') + delta } : m));
        };
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buffer.indexOf('\n')) !== -1) {
            const line = buffer.slice(0, idx).trim();
            buffer = buffer.slice(idx + 1);
            if (!line) continue;
            try {
              const obj = JSON.parse(line);
              if (obj.delta) appendDelta(obj.delta);
              if (obj.error) throw new Error(obj.error);
              if (obj.done && obj.full) {
                // Ensure final content
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: obj.full } : m));
              }
            } catch (e) {
              appendDelta(line);
            }
          }
        }
        setIsSending(false);
        setAbortController(null);
      } catch (error: any) {
        console.error('Error sending message:', {
          error,
          name: error.name,
          message: error.message,
          stack: error.stack,
          response: error.response || 'No response object'
        });

        // Remove the temporary message on error
        setMessages(prev => prev.filter(msg => !msg.id || msg.id !== tempMessageId));

        // Show user-friendly error message
        let errorMessage = 'Error al enviar el mensaje. Por favor, inténtalo de nuevo.';

        if (error.message.includes('Failed to fetch')) {
          errorMessage = 'No se pudo conectar con el servidor. Verifica tu conexión a internet.';
        } else if (error.response?.data?.detail) {
          // Use the error detail from the backend if available
          errorMessage = error.response.data.detail;
        } else if (error.message.includes('404')) {
          errorMessage = 'El agente no fue encontrado o no es un modelo Ollama válido.';
        } else if (error.message.includes('401') || error.message.includes('403')) {
          errorMessage = 'No tienes permiso para realizar esta acción. Por favor, inicia sesión de nuevo.';
        } else if (error.message) {
          errorMessage = error.message;
        }

        toast.error(errorMessage);
        setIsSending(false);
        setAbortController(null);
      }
    } catch (error: any) {
      console.error('Unexpected error in handleSendMessage:', error);
      toast.error('Ocurrió un error inesperado al procesar la solicitud');
      setIsSending(false);
      setAbortController(null);
    }
  };

  const cancelStreaming = () => {
    if (abortController) {
      abortController.abort();
      setIsSending(false);
      setAbortController(null);
    }
  };

  const startVoiceInteraction = async () => {
    try {
      if (isRecording) {
        // Stop recording logic is handled in the button click
        return;
      }

      setIsRecording(true);
      setError(null);

      // 1. Get Microphone Stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // 2. Start Recording
      const mr = new MediaRecorder(stream, { mimeType: 'audio/wav' });
      mediaRecorderRef.current = mr;
      const chunks: Blob[] = [];

      mr.ondataavailable = (e: any) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mr.onstop = async () => {
        // Stop tracks
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;

        const blob = new Blob(chunks, { type: 'audio/wav' });

        // Check if blob is too small (silence/click)
        if (blob.size < 1000) {
          setIsRecording(false);
          return;
        }

        setIsVoiceProcessing(true);
        setIsRecording(false);

        try {
          // 3. STT
          const formData = new FormData();
          formData.append('audio', blob, 'recording.wav');

          // Use absolute URL for STT
          const sttResp = await fetch(`${API_URL}/calls/stt/transcribe`, {
            method: 'POST',
            body: formData,
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            }
          });

          if (!sttResp.ok) throw new Error('STT failed');
          const sttData = await sttResp.json();
          const userText = sttData.text || sttData.transcript; // Handle both potential response keys
          setSttTranscript(userText);

          // Add to voice messages
          setVoiceMessages(prev => [...prev, { role: 'user', content: userText }]);

          // 4. Chat with Agent
          const history = voiceMessages.map(m => ({ role: m.role, content: m.content }));
          history.push({ role: 'user', content: userText });

          const chatResp = await fetch(`${API_URL}/agents/ollama/${id}/chat/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
            },
            body: JSON.stringify({
              message: userText,
              conversation_history: history
            })
          });

          if (!chatResp.ok) throw new Error('Chat failed');

          // Parse Stream
          const reader = chatResp.body?.getReader();
          const decoder = new TextDecoder();
          let fullResponse = '';

          if (reader) {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split('\\n');

              for (const line of lines) {
                if (!line.trim()) continue;
                try {
                  const json = JSON.parse(line);
                  if (json.delta) {
                    fullResponse += json.delta;
                  }
                  if (json.done && json.full) {
                    fullResponse = json.full;
                  }
                } catch (e) {
                  // ignore parse errors for partial chunks
                }
              }
            }
          }

          setVoiceMessages(prev => [...prev, { role: 'assistant', content: fullResponse }]);

          // 5. TTS
          if (fullResponse.trim()) {
            const ttsResp = await fetch(`${API_URL}/calls/tts/generate`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
              },
              body: JSON.stringify({ text: fullResponse })
            });

            if (!ttsResp.ok) throw new Error('TTS failed');
            const ttsData = await ttsResp.json();

            // 6. Play Audio
            if (ttsData.audio_url) {
              // Ensure previous audio is stopped
              if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
              }

              const audio = new Audio(ttsData.audio_url);
              audioRef.current = audio;

              // Auto-restart recording when audio ends
              audio.onended = () => {
                setIsVoiceProcessing(false);
                // Recursive call to start listening again
                startVoiceInteraction();
              };

              audio.onerror = (e) => {
                console.error("Audio playback error", e);
                setIsVoiceProcessing(false);
                toast.error("Error al reproducir audio");
              };

              await audio.play();
            } else {
              setIsVoiceProcessing(false);
            }
          } else {
            setIsVoiceProcessing(false);
          }

        } catch (error) {
          console.error('Voice interaction error:', error);
          toast.error('Error en la interacción de voz');
          setIsVoiceProcessing(false);
          setIsRecording(false);
        }
      };

      mr.start();

    } catch (error) {
      console.error('Error starting voice interaction:', error);
      toast.error('No se pudo acceder al micrófono');
      setIsRecording(false);
    }
  };

  if (isLoading) {
    return (
      <AgentLayout title="Cargando agente...">
        <div className="flex items-center justify-center h-64">
          <div className="bg-white/50 backdrop-blur-sm p-6 rounded-xl shadow">
            <Loader2 className="h-8 w-8 animate-spin text-foreground mx-auto mb-2" />
            <span>Cargando agente...</span>
          </div>
        </div>
      </AgentLayout>
    );
  }

  if (!agent) {
    return (
      <AgentLayout title="Agente no encontrado">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="bg-white/50 backdrop-blur-sm p-6 rounded-xl shadow">
            <h2 className="text-xl font-semibold mb-2">Agente no encontrado</h2>
            <p className="mb-4">El agente solicitado no existe o no tienes permiso para verlo.</p>
            <Button
              onClick={() => navigate('/dashboard/agentes')}
              className="mt-2"
              variant="outline"
            >
              Volver a la lista de agentes
            </Button>
          </div>
        </div>
      </AgentLayout>
    );
  }

  return (
    <Tabs value={tabValue} onValueChange={setTabValue} className="w-full">
      <AgentLayout
        title={`${agent.name}`}
        headerCenter={
          <nav className="flex items-center justify-center gap-6">
            <button
              className={`px-3 py-2 rounded-md ${tabValue === 'chat' ? 'text-primary font-semibold' : 'text-gray-600 hover:text-gray-800'}`}
              onClick={() => setTabValue('chat')}
            >
              <span className="inline-flex items-center">Chat</span>
            </button>
            <button
              className={`px-3 py-2 rounded-md ${tabValue === 'voice' ? 'text-primary font-semibold' : 'text-gray-600 hover:text-gray-800'}`}
              onClick={() => setTabValue('voice')}
            >
              <span className="inline-flex items-center">Llamada Web</span>
            </button>
            <button
              className={`px-3 py-2 rounded-md ${tabValue === 'config' ? 'text-primary font-semibold' : 'text-gray-600 hover:text-gray-800'}`}
              onClick={() => setTabValue('config')}
            >
              <span className="inline-flex items-center">Configuración</span>
            </button>
          </nav>
        }
        headerRight={
          isEditing ? (
            <div className="flex gap-2">
              <Button
                onClick={handleSave}
                disabled={isSaving}
                className="bg-primary text-white hover:bg-primary/90"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Guardar cambios
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setIsEditing(false);
                  setError(null);
                  if (agent) {
                    setFormData({ ...agent });
                  }
                }}
                disabled={isSaving}
                className="border-input bg-background hover:bg-accent hover:text-accent-foreground"
              >
                Cancelar
              </Button>
            </div>
          ) : (
            <Button
              onClick={() => setIsEditing(true)}
              variant="outline"
              className="border-input bg-background hover:bg-accent hover:text-accent-foreground"
            >
              <Settings className="mr-2 h-4 w-4" />
              Editar agente
            </Button>
          )
        }
      >
        <div className="container mx-auto p-4 pt-6 md:p-6 lg:p-8 xl:p-10 space-y-6">
          {error && (
            <div className="bg-white/50 backdrop-blur-sm p-4 rounded-xl shadow">
              <div className="text-sm text-red-600">
                {error}
              </div>
            </div>
          )}

          <TabsContent value="chat" className="mt-2">
            <div className="h-[70vh] overflow-y-auto mb-4 space-y-4 p-4 pb-24 flex flex-col">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <p>Envía un mensaje a tu agente</p>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[60ch] w-auto px-4 py-3 ${msg.role === 'user' ? 'rounded-2xl bg-primary text-white' : 'bg-transparent text-foreground'
                        }`}
                    >
                      {typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}
                    </div>
                  </div>
                ))
              )}
            </div>
            {/* Input abajo fijo */}
            <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl flex items-center gap-2 bg-white/80 backdrop-blur-md shadow-lg rounded-full px-4 py-2 border border-white/30">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Escribe un mensaje..."
                onKeyDown={(e) => e.key === 'Enter' && !isSending && handleSendMessage()}
                className="flex-1 bg-transparent border-none focus:outline-none"
                disabled={isSending}
              />
              {isSending ? (
                <Button onClick={cancelStreaming} className="rounded-full px-4 bg-primary text-white hover:bg-primary/90">Cancelar</Button>
              ) : (
                <Button onClick={handleSendMessage} className="rounded-full px-4 bg-primary text-white hover:bg-primary/90">Enviar</Button>
              )}
            </div>
          </TabsContent>

          <TabsContent value="config" className="mt-6">
            <Card className="bg-white/50 backdrop-blur-sm border border-white/20">
              <CardHeader>
                <CardTitle>Configuración del Agente</CardTitle>
                <CardDescription>
                  Configura los parámetros básicos de tu agente de IA
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="name">Nombre</Label>
                    <Input
                      id="name"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model">Modelo</Label>
                    <Input
                      id="model"
                      value={formData.model || ''}
                      onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="temperature" className="text-foreground">Temperatura: {formData.temperature}</Label>
                    <Input
                      id="temperature"
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={formData.temperature || 0.7}
                      onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="max_tokens" className="text-foreground">Máximo de tokens: {formData.max_tokens}</Label>
                    <Input
                      id="max_tokens"
                      type="range"
                      min="100"
                      max="4000"
                      step="100"
                      value={formData.max_tokens || 2000}
                      onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                      disabled={!isEditing}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description" className="text-foreground">Descripción</Label>
                  <Input
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="system_prompt" className="text-foreground">Instrucciones del sistema</Label>
                  <Textarea
                    id="system_prompt"
                    value={formData.system_prompt || ''}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    disabled={!isEditing}
                    className="min-h-[200px]"
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="voice" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[80vh]">
              {/* Mitad izquierda - Animación de voz y controles */}
              <div className="bg-white/40 backdrop-blur-lg rounded-2xl border border-white/20 p-8 flex flex-col items-center justify-center space-y-8">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-black mb-2">Llamada Web</h2>
                  <p className="text-black/70">Habla con tu agente usando voz</p>
                </div>

                {/* Animación circular para el estado de voz */}
                <div className="relative w-48 h-48 flex items-center justify-center">
                  {/* Círculo exterior con animación */}
                  <div className={`absolute inset-0 rounded-full border-4 transition-all duration-300 ${isRecording ? 'border-red-400 animate-pulse' :
                    isVoiceProcessing ? 'border-blue-400 animate-spin' :
                      'border-black/30'
                    }`}>
                    {/* Ondas de sonido cuando está grabando */}
                    {isRecording && (
                      <>
                        <div className="absolute inset-2 rounded-full border-2 border-red-300 animate-ping"></div>
                        <div className="absolute inset-4 rounded-full border-2 border-red-200 animate-ping animation-delay-200"></div>
                      </>
                    )}
                    {/* Efecto de procesamiento cuando la IA habla */}
                    {isVoiceProcessing && (
                      <>
                        <div className="absolute inset-2 rounded-full border-2 border-blue-300 animate-pulse"></div>
                        <div className="absolute inset-6 rounded-full border border-blue-200 animate-pulse animation-delay-300"></div>
                      </>
                    )}
                  </div>

                  {/* Círculo interior con icono */}
                  <div className={`w-32 h-32 rounded-full flex items-center justify-center shadow-2xl backdrop-blur-sm transition-all duration-300 ${isRecording ? 'bg-red-500/80' :
                    isVoiceProcessing ? 'bg-blue-500/80' :
                      'bg-black/20'
                    }`}>
                    {isRecording ? (
                      <svg className="w-12 h-12 text-black" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                      </svg>
                    ) : isVoiceProcessing ? (
                      <svg className="w-12 h-12 text-black animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.793L4.617 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.617l3.766-3.793a1 1 0 011.617.793zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-12 h-12 text-black" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0A7.001 7.001 0 0015 14.93z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </div>

                {/* Estado actual */}
                <div className="text-center space-y-2">
                  <div className={`text-lg font-medium ${isRecording ? 'text-red-600' :
                    isVoiceProcessing ? 'text-blue-600' :
                      'text-black/80'
                    }`}>
                    {isRecording ? 'Grabando...' :
                      isVoiceProcessing ? 'Procesando...' :
                        'Listo para hablar'}
                  </div>
                  {sttTranscript && (
                    <div className="text-sm text-black/60 max-w-md mx-auto">
                      "{sttTranscript}"
                    </div>
                  )}
                </div>

                {/* Botón principal */}
                <button
                  onClick={async () => {
                    if (!ttsAvailable || isVoiceProcessing) return;

                    if (isRecording) {
                      // Detener grabación manual
                      setIsRecording(false);
                      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                        mediaRecorderRef.current.stop();
                      }
                      // Detener cualquier audio en reproducción
                      if (audioRef.current) {
                        audioRef.current.pause();
                        audioRef.current.currentTime = 0;
                      }
                    } else {
                      // Iniciar ciclo de conversación
                      startVoiceInteraction();
                    }
                  }}
                  disabled={!ttsAvailable || isVoiceProcessing}
                  className={`w-20 h-20 rounded-full flex items-center justify-center shadow-lg backdrop-blur-sm transition-all duration-300 ${isRecording ? 'bg-red-500/90 hover:bg-red-600/90' :
                    isVoiceProcessing ? 'bg-blue-500/90 hover:bg-blue-600/90' :
                      'bg-gray-800/90 hover:bg-gray-900/80'
                    } text-black hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100`}
                >
                  {isRecording ? (
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                    </svg>
                  ) : isVoiceProcessing ? (
                    <svg className="w-8 h-8 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.793L4.617 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.617l3.766-3.793a1 1 0 011.617.793zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0A7.001 7.001 0 0015 14.93z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>

                {!ttsAvailable && (
                  <div className="text-sm text-red-300 bg-red-500/20 backdrop-blur-sm rounded-lg px-4 py-2">
                    Servicio de voz no disponible
                  </div>
                )}
              </div>

              {/* Mitad derecha - Chat de transcripción */}
              <div className="bg-white/40 backdrop-blur-lg rounded-2xl border border-white/20 p-6 flex flex-col">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-black mb-2">Transcripción</h3>
                  <p className="text-black/70 text-sm">Conversación de voz a texto</p>
                </div>

                {/* Área de transcripción */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                  {voiceMessages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-black/50">
                      <svg className="w-12 h-12 mb-4 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0A7.001 7.001 0 0015 14.93z" clipRule="evenodd" />
                      </svg>
                      <p className="text-center text-black">Comienza a hablar para ver la transcripción</p>
                    </div>
                  ) : (
                    voiceMessages.map((msg, index) => (
                      <div key={index} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] w-auto px-4 py-3 rounded-2xl backdrop-blur-sm ${msg.role === 'user'
                          ? 'bg-white/60 text-black border border-black/20'
                          : 'bg-black/10 text-black border border-black/10'
                          }`}>
                          <div className="text-sm mb-1 opacity-70 font-medium">
                            {msg.role === 'user' ? 'Tú' : 'IA'}
                          </div>
                          <div className="text-base">{msg.content}</div>
                        </div>
                      </div>
                    ))
                  )}

                  {/* Mensaje temporal mientras se procesa */}
                  {isVoiceProcessing && (
                    <div className="flex justify-start">
                      <div className="max-w-[80%] w-auto px-4 py-3 rounded-2xl bg-black/10 text-black border border-black/10">
                        <div className="text-sm mb-1 opacity-70 font-medium">IA</div>
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-black/60 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-black/60 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-black/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>
        </div>
      </AgentLayout >
    </Tabs >
  );
}

export default AgentDetailPage;
