import React, { useState, useEffect } from 'react';
import { 
  Database, 
  MessageCircle, 
  Bot,
  FileText,
  Search,
  Upload,
  BarChart3
} from 'lucide-react';
import KnowledgeBase from '../components/KnowledgeBase';
import OllamaChatWithKnowledge from '../components/OllamaChatWithKnowledge';
import { apiClient } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface Agent {
  id: number;
  name: string;
  description?: string;
  model_name: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user_id: number;
  agent_type: string;
  model_config?: Record<string, any>;
  capabilities?: string[];
}

type ViewMode = 'knowledge' | 'chat';

export const KnowledgeBasePage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('knowledge');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getAgents();
      if (response.data) {
        setAgents(response.data);
        // Select first agent by default
        if (response.data.length > 0) {
          setSelectedAgent(response.data[0]);
        }
      }
    } catch (err: any) {
      console.error('Error loading agents:', err);
      setError('Error al cargar los agentes');
    } finally {
      setLoading(false);
    }
  };

  const handleChatWithAgent = (agent: Agent) => {
    setSelectedAgent(agent);
    setViewMode('chat');
  };

  const handleBackToKnowledge = () => {
    setViewMode('knowledge');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Database className="mx-auto w-12 h-12 text-blue-600 mb-4 animate-pulse" />
          <p className="text-gray-600">Cargando Knowledge Base...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadAgents}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'chat' && selectedAgent) {
    return (
      <div className="h-screen">
        <OllamaChatWithKnowledge
          agentId={selectedAgent.id}
          agentName={selectedAgent.name}
          modelName={selectedAgent.model_name}
          onBack={handleBackToKnowledge}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Knowledge Base</h1>
                <p className="text-sm text-gray-500">Gestiona documentos y chatea con IA</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Agent Selection for Chat */}
              {agents.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Agente:</span>
                  <select
                    value={selectedAgent?.id || ''}
                    onChange={(e) => {
                      const agent = agents.find(a => a.id === parseInt(e.target.value));
                      setSelectedAgent(agent || null);
                    }}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {agents.map(agent => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.model_name})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Chat Button */}
              {selectedAgent && (
                <button
                  onClick={() => handleChatWithAgent(selectedAgent)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <MessageCircle className="w-4 h-4" />
                  Chat con IA
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Documentos</p>
                <p className="text-2xl font-semibold text-gray-900">-</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Search className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Búsquedas</p>
                <p className="text-2xl font-semibold text-gray-900">-</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Bot className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Agentes</p>
                <p className="text-2xl font-semibold text-gray-900">{agents.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <BarChart3 className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Chunks</p>
                <p className="text-2xl font-semibold text-gray-900">-</p>
              </div>
            </div>
          </div>
        </div>

        {/* Knowledge Base Component */}
        <div className="bg-white rounded-lg border border-gray-200">
          {selectedAgent ? (
            <KnowledgeBase agent={selectedAgent} />
          ) : (
            <div className="p-8 text-center text-gray-500">
              <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Selecciona un agente para gestionar su base de conocimiento</p>
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-blue-50 rounded-lg border border-blue-200 p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            ¿Cómo usar el Knowledge Base?
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-800">
            <div className="flex items-start gap-2">
              <Upload className="w-4 h-4 mt-0.5 text-blue-600" />
              <div>
                <p className="font-medium">1. Sube documentos</p>
                <p>Arrastra archivos PDF, TXT o DOCX para añadirlos a la base de conocimiento.</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Search className="w-4 h-4 mt-0.5 text-blue-600" />
              <div>
                <p className="font-medium">2. Busca información</p>
                <p>Usa la búsqueda semántica para encontrar contenido relevante en tus documentos.</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <MessageCircle className="w-4 h-4 mt-0.5 text-blue-600" />
              <div>
                <p className="font-medium">3. Chatea con IA</p>
                <p>Haz preguntas y obtén respuestas basadas en tus documentos usando RAG.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBasePage;