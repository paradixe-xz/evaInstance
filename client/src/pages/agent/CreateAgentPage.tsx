import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { API_BASE_URL } from '../../config/api';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { toast } from 'sonner';
import { AgentLayout } from '../../components/layout/AgentLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { ChevronRight, ChevronLeft, CheckCircle, Loader2 } from 'lucide-react';

// AIAgent interface for type safety
interface AIAgent {
  id?: number;
  name: string;
  description: string;
  model: string;
  agent_type: 'whatsapp' | 'web' | 'email' | 'ollama';
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  status: 'draft' | 'active' | 'inactive';
  is_active: boolean;
  is_ollama_model?: boolean;
  ollama_model_name?: string | null;
  base_model?: string;
  num_ctx?: number;
  modelfile_content?: string | null;
  custom_template?: string | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: any; // For any additional properties
}

// Available Ollama models
const AVAILABLE_MODELS = [
  'llama2',
  'llama3',
  'mistral',
  'codellama',
  'llava',
  'gemma',
  'phi',
  'neural-chat',
  'solar',
  'mixtral',
  'command-r',
  'command-r-plus'
];

const API_URL = API_BASE_URL;

const steps = [
  {
    id: 'basic',
    title: 'Información Básica',
    fields: ['name', 'description']
  },
  {
    id: 'configuration',
    title: 'Configuración',
    fields: ['model', 'agent_type', 'temperature']
  },
  {
    id: 'prompt',
    title: 'Instrucciones',
    fields: ['system_prompt']
  },
  {
    id: 'review',
    title: 'Revisión',
    fields: []
  }
];

export function CreateAgentPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [agent, setAgent] = useState<AIAgent>({
    name: '',
    description: '',
    model: 'llama3',
    agent_type: 'whatsapp',
    system_prompt: 'Eres un asistente útil y amable.',
    temperature: 0.7,
    max_tokens: 2000,
    status: 'draft',
    is_active: true
  });

  const navigate = useNavigate();
  const { logout } = useAuth();

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setAgent(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setAgent(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (currentStep < steps.length - 1) {
      nextStep();
      return;
    }
    
    // Prepare agent data according to backend schema
    const agentData = {
      name: agent.name,
      description: agent.description || '',
      agent_type: 'whatsapp',
      model: agent.model,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      system_prompt: agent.system_prompt,
      is_ollama_model: true,  // Always set to true for Ollama models
      ollama_model_name: agent.model,  // Use the selected model as the Ollama model name
      base_model: agent.model,  // The base model to use
      num_ctx: 4096,  // Default context window size
      conversation_style: 'professional',
      response_time_limit: 30,
      voice_speed: 1.0,
      voice_pitch: 1.0,
      // Initialize optional fields
      workflow_steps: null,
      conversation_structure: null,
      modelfile_content: null,
      custom_template: null,
      ollama_parameters: {
        model: agent.model,
        temperature: agent.temperature,
        system: agent.system_prompt
      },
      personality_traits: null,
      // Required fields with default values
      status: 'active',
      is_active: true,
      total_interactions: 0,
      successful_interactions: 0,
      success_rate: 0.0,
      avg_interaction_duration: 0.0,
      avg_response_time: 0.0,
      total_cost: 0.0,
      feedback_score: 0.0,
      
    };
    
    setIsCreating(true);
    try {
      // Always create an Ollama model for now
      const ollamaData = {
        name: agent.name.toLowerCase().replace(/\s+/g, '-'),  // Convert name to URL-friendly format
        base_model: agent.model || 'llama3',
        system_prompt: agent.system_prompt || 'Eres un asistente útil.',
        temperature: agent.temperature || 0.7,
        num_ctx: 4096,
        agent_type: 'whatsapp',
        custom_template: agent.custom_template || null
      };
      
      // First create the Ollama model
      const createResponse = await api.post(`${API_URL}/agents/ollama/create`, ollamaData);
      
      if (!createResponse.data || !createResponse.data.agent_id) {
        throw new Error('No se pudo crear el modelo Ollama');
      }
      
      // Then update the agent with the Ollama model details
      const agentResponse = await api.put(`${API_URL}/agents/${createResponse.data.agent_id}`, {
        ...agentData,
        ollama_model_name: createResponse.data.model_name || agent.model,
        is_ollama_model: true,
        agent_type: 'whatsapp'
      });
      
      toast.success('Agente con modelo Ollama creado exitosamente');
      navigate(`/dashboard/agentes/${createResponse.data.agent_id}`);
    } catch (error: any) {
      console.error('Error al crear el agente:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Error al crear el agente';
      toast.error(errorMessage);
      
      // If unauthorized, redirect to login
      if (error.response?.status === 401) {
        logout();
        navigate('/login');
      }
    } finally {
      setIsCreating(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Info
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre del Agente *</Label>
              <Input
                id="name"
                name="name"
                value={agent.name}
                onChange={handleChange}
                placeholder="Ej: Asistente de Ventas"
                required
                className="bg-white/50 backdrop-blur-sm"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descripción</Label>
              <Textarea
                id="description"
                name="description"
                value={agent.description}
                onChange={handleChange}
                placeholder="Describe el propósito de este agente"
                rows={3}
                className="bg-white/50 backdrop-blur-sm"
              />
            </div>
          </div>
        );
      
      case 1: // Configuration
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="model">Modelo de IA *</Label>
                <Select
                  value={agent.model}
                  onValueChange={(value) => handleSelectChange('model', value)}
                >
                  <SelectTrigger className="bg-white/50 backdrop-blur-sm">
                    <SelectValue placeholder="Selecciona un modelo" />
                  </SelectTrigger>
                  <SelectContent>
{AVAILABLE_MODELS.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="agent_type">Tipo de Agente *</Label>
                <Select
                  value={agent.agent_type}
                  onValueChange={(value) => handleSelectChange('agent_type', value)}
                >
                  <SelectTrigger className="bg-white/50 backdrop-blur-sm">
                    <SelectValue placeholder="Selecciona un tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="web">Web</SelectItem>
                    <SelectItem value="email">Correo Electrónico</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <Label htmlFor="temperature">Temperatura: {agent.temperature}</Label>
              <Input
                id="temperature"
                name="temperature"
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={agent.temperature}
                onChange={(e) => handleSelectChange('temperature', e.target.value)}
                className="w-full h-2 bg-white/50 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Preciso</span>
                <span>Creativo</span>
              </div>
            </div>
          </div>
        );
      
      case 2: // Prompt
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="system_prompt">Instrucciones del Sistema *</Label>
              <Textarea
                id="system_prompt"
                name="system_prompt"
                value={agent.system_prompt}
                onChange={handleChange}
                placeholder="Escribe las instrucciones para el agente"
                rows={8}
                required
                className="bg-white/50 backdrop-blur-sm"
              />
              <p className="text-sm text-gray-500 mt-2">
                Estas instrucciones guiarán el comportamiento del agente. Sé claro y específico sobre su personalidad, tono y funciones.
              </p>
            </div>
          </div>
        );
      
      case 3: // Review
        return (
          <div className="space-y-6">
            <Card className="bg-white/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg">Resumen del Agente</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Nombre</h3>
                  <p className="mt-1">{agent.name || 'No especificado'}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Descripción</h3>
                  <p className="mt-1">{agent.description || 'No especificada'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Modelo</h3>
                    <p className="mt-1">{agent.model}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Tipo</h3>
                    <p className="mt-1 capitalize">{agent.agent_type}</p>
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Temperatura</h3>
                  <p className="mt-1">{agent.temperature}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      
      default:
        return null;
    }
  };

  const isLastStep = currentStep === steps.length - 1;

  return (
    <AgentLayout
      title="Nuevo Agente de IA"
      showBackButton={true}
    >
      <div className="w-full max-w-4xl mx-auto p-6">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Enhanced step indicator with connecting line */}
          <div className="relative mb-12">
            <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-gray-200 -translate-y-1/2 z-0 -mt-2.5"></div>
            <div className="relative flex justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex flex-col items-center z-10">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                      currentStep >= index
                        ? 'bg-primary border-primary text-white'
                        : 'bg-white border-gray-300 text-gray-600'
                    }`}
                  >
                    {currentStep > index ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  <span 
                    className={`mt-2 text-sm font-medium ${
                      currentStep === index ? 'text-primary' : 'text-gray-600'
                    }`}
                  >
                    {step.title}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Form Content */}
          <Card className="bg-white/50 backdrop-blur-sm border-0 shadow-sm">
            <CardContent className="pt-6">
              {renderStepContent()}
              
              {/* Navigation buttons */}
              <div className="flex justify-between pt-8 border-t border-gray-200 mt-8">
                <Button
                  type="button"
                  variant="outline"
                  onClick={prevStep}
                  disabled={currentStep === 0 || isCreating}
                  className={`${currentStep === 0 ? 'invisible' : ''} bg-white hover:bg-gray-50`}
                >
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Anterior
                </Button>
                
                <Button 
                  type={isLastStep ? 'submit' : 'button'}
                  onClick={!isLastStep ? nextStep : undefined}
                  className="bg-black text-white hover:bg-gray-800 px-6"
                  disabled={isCreating}
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creando...
                    </>
                  ) : isLastStep ? (
                    'Crear Agente'
                  ) : (
                    <>
                      Siguiente
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      </div>
    </AgentLayout>
  );
}
