import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { apiClient, type OllamaModelResponse, type OllamaModelCreate } from '../services/api';
import { Save, ArrowLeft } from 'lucide-react';
import BrandLoader from '../components/ui/BrandLoader';

const AgentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [agent, setAgent] = useState<OllamaModelResponse | null>(null);
  const [activeTab, setActiveTab] = useState('info');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{role: string, content: string}>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // STT/TTS for Web Call Test
  const recognitionRef = useRef<any>(null);
  const [supportsSTT, setSupportsSTT] = useState(false);
  const [listening, setListening] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [callResponse, setCallResponse] = useState<string | null>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    setSupportsSTT(!!SpeechRecognition);
  }, []);

  useEffect(() => {
    const fetchAgent = async () => {
      if (!id) {
        setError('No se proporcionó un ID de agente');
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiClient.getOllamaModels();
        console.log('API Response:', response); // Debug log
        
        // Extraer modelos desde response.data
        let models: OllamaModelResponse[] = [];
        if (response.error) {
          throw new Error(response.error);
        }
        const data = response.data;
        if (Array.isArray(data)) {
          models = data;
        } else if (data && typeof data === 'object') {
          if ('models' in data && Array.isArray((data as any).models)) {
            models = (data as any).models as OllamaModelResponse[];
          } else {
            // Fallback: intentar encontrar la primera propiedad que sea un array
            const arrayKey = Object.keys(data).find(
              (key) => Array.isArray((data as any)[key])
            );
            if (arrayKey) {
              models = ((data as any)[arrayKey] as any[]);
            }
          }
        }
        
        console.log('Models:', models); // Debug log
        
        // Buscar el agente por ID o nombre
        const foundAgent = models.find((model: OllamaModelResponse) => 
          String(model.id) === String(id) || 
          String(model.name) === String(id)
        );
        
        console.log('Found Agent:', foundAgent); // Debug log
        
        if (foundAgent) {
          setAgent(foundAgent);
        } else {
          setError(`No se encontró el agente con el ID: ${id}`);
          console.error('Agent not found. Available models:', models);
        }
      } catch (err) {
        console.error('Error fetching agent:', err);
        setError('Error al cargar los datos del agente');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgent();
  }, [id]);

  const handleSave = async () => {
    if (!agent || !id) return;
    
    setSaving(true);
    setError(null);
    
    try {
      const updateData: OllamaModelCreate = {
        name: agent.name,
        base_model: agent.base_model,
        system_prompt: agent.system_prompt,
        temperature: agent.temperature,
        num_ctx: agent.num_ctx,
        custom_template: agent.custom_template || undefined
      };
      
      const response = await apiClient.updateOllamaModel(id, updateData);
      if (response.data) {
        setAgent(prev => prev ? { ...prev, ...response.data } : null);
        // You might want to show a success toast here
      } else if (response.error) {
        setError(response.error);
      }
    } catch (err) {
      console.error('Error saving agent:', err);
      setError('Failed to save agent');
    } finally {
      setSaving(false);
    }
  };

  const handleChatSend = async () => {
    if (!message.trim() || !id) return;
    
    const userMessage = { role: 'user' as const, content: message };
    const updatedHistory = [...chatHistory, userMessage];
    
    setChatHistory(updatedHistory);
    setMessage('');
    
    try {
      const response = await apiClient.chatWithOllamaModel(
        parseInt(id),
        message,
        updatedHistory
      );
      
      if (response.data) {
        setChatHistory(prev => [
          ...prev, 
          { role: 'assistant' as const, content: (response.data as any)?.message || 'No response' }
        ]);
      } else if (response.error) {
        setError(response.error);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message');
    }
  };

  // Web Call Test actions
  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    if (!recognitionRef.current) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'es-ES';
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.onresult = (event: any) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        setMessage(transcript);
      };
      recognition.onend = () => setListening(false);
      recognition.onerror = () => setListening(false);
      recognitionRef.current = recognition;
    }
    setListening(true);
    try { recognitionRef.current.start(); } catch {}
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
    }
  };

  const speak = (text: string) => {
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'es-ES';
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('TTS no disponible:', e);
    }
  };

  const handleWebCall = async () => {
    if (!message.trim() || !id) return;
    setIsCalling(true);
    setError(null);
    setCallResponse(null);
    try {
      const response = await apiClient.chatWithOllamaModel(parseInt(id), message);
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        const resp = (response.data.response || (response.data as any).ai_response || (response.data as any).message || '').toString();
        setCallResponse(resp);
        speak(resp);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error en la llamada web');
    } finally {
      setIsCalling(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <BrandLoader size="lg" />
          <h1 className="text-2xl font-bold text-slate-900 mt-6">Cargando...</h1>
        </div>
      </div>
    );
  }

  if (!agent || error) {
    return (
      <div className="container mx-auto p-6">
        <Button 
          variant="ghost" 
          onClick={() => navigate(-1)}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Agents
        </Button>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            {error || 'Agent not found'}
          </h2>
          <p className="text-muted-foreground">
            The agent you're looking for doesn't exist or you don't have permission to view it.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Agents
      </Button>
      
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{agent.name}</h1>
        <p className="text-muted-foreground">Manage your agent settings and test interactions</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="info">Agent Info</TabsTrigger>
          <TabsTrigger value="chat">Chat Test</TabsTrigger>
          <TabsTrigger value="call">Web Call Test</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
              <CardDescription>Update your agent's settings and behavior.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <Input
                  value={agent.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                    setAgent(prev => prev ? { ...prev, name: e.target.value } : null)
                  }
                  disabled={saving}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Base Model</label>
                <Input
                  value={agent.base_model}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
                    setAgent(prev => prev ? { ...prev, base_model: e.target.value } : null)
                  }
                  disabled={saving}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">System Prompt</label>
                <Textarea
                  value={agent.system_prompt}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                    setAgent(prev => prev ? { ...prev, system_prompt: e.target.value } : null)
                  }
                  rows={6}
                  disabled={saving}
                  className="font-mono text-sm"
                />
              </div>
              <div className="flex justify-end">
                <Button 
                  onClick={handleSave} 
                  disabled={saving || !agent?.name || !agent?.base_model || !agent?.system_prompt}
                >
                  {saving ? (
                    <>
                      <BrandLoader size="sm" className="mr-2" />
                      Guardando...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chat">
          <Card>
            <CardHeader>
              <CardTitle>Chat Test</CardTitle>
              <CardDescription>Test your agent's chat capabilities</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border rounded-lg p-4 h-64 overflow-y-auto bg-gray-50">
                {chatHistory.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-gray-400">
                    No messages yet. Start a conversation!
                  </div>
                ) : (
                  chatHistory.map((msg, i) => (
                    <div 
                      key={i} 
                      className={`mb-2 p-3 rounded-lg ${msg.role === 'user' ? 'bg-white border border-gray-200' : 'bg-blue-50'}`}
                    >
                      <div className="font-medium text-sm text-gray-500 mb-1">
                        {msg.role === 'user' ? 'You' : agent?.name || 'Assistant'}
                      </div>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  ))
                )}
              </div>
              <div className="flex gap-2">
                <Input
                  value={message}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMessage(e.target.value)}
                  onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => 
                    e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleChatSend())
                  }
                  placeholder={`Message ${agent?.name || 'the agent'}...`}
                  disabled={saving}
                  className="flex-1"
                />
                <Button 
                  onClick={handleChatSend}
                  disabled={!message.trim() || saving}
                >
                  Send
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="call">
          <Card>
            <CardHeader>
              <CardTitle>Web Call Test</CardTitle>
              <CardDescription>Prueba la llamada web con voz usando el modelo interno</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-primary/5 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <Button onClick={startListening} disabled={listening || !supportsSTT}>
                    {listening ? 'Escuchando…' : '🎤 Hablar'}
                  </Button>
                  <Button variant="outline" onClick={stopListening} disabled={!listening}>
                    Detener
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    {supportsSTT ? (listening ? 'STT activo' : 'STT disponible') : 'STT no soportado'}
                  </span>
                </div>

                <label className="block text-sm font-medium mb-1">Mensaje</label>
                <Textarea
                  value={message}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
                  rows={4}
                  placeholder="Di algo o escribe tu mensaje para el agente"
                  className="font-mono"
                />

                <div className="flex items-center gap-3 mt-2">
                  <Button onClick={handleWebCall} disabled={!message.trim() || isCalling}>
                    Hacer llamada web
                  </Button>
                  {isCalling && <BrandLoader size="sm" label="Llamando..." />}
                </div>

                {callResponse && (
                  <div className="mt-4 border rounded-lg p-3 bg-white">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">Respuesta</h3>
                      <Button size="sm" variant="outline" onClick={() => speak(callResponse)}>
                        🔊 Escuchar respuesta
                      </Button>
                    </div>
                    <p className="mt-2 whitespace-pre-wrap">{callResponse}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentDetailPage;
