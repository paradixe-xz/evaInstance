import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Cpu,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Edit,
  MessageCircle,
  ExternalLink
} from 'lucide-react';
import BrandLoader from './ui/BrandLoader';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import type { OllamaModelResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import OllamaChat from './OllamaChat';
import { Button } from './ui/button';

interface OllamaModelForm {
  name: string;
  base_model: string;
  system_prompt: string;
  temperature: number;
  num_ctx: number;
  custom_template: string;
}

const OllamaModelManager: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [models, setModels] = useState<any[]>([]);
  const [availableBaseModels, setAvailableBaseModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [selectedModel, setSelectedModel] = useState<any>(null);

  const [formData, setFormData] = useState<OllamaModelForm>({
    name: '',
    base_model: 'llama3.2:3b',
    system_prompt: 'Eres un asistente útil y amigable.',
    temperature: 0.7,
    num_ctx: 2048,
    custom_template: ''
  });

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadOllamaModels();
      loadAvailableBaseModels();
    }
  }, [authLoading, isAuthenticated]);

  const loadAvailableBaseModels = async () => {
    try {
      const response = await apiClient.getOllamaBaseModels();
      if (response.data && response.data.base_models && Array.isArray(response.data.base_models)) {
        // Extraer solo los nombres de los modelos
        const modelNames = response.data.base_models.map((model: any) => model.name || model);
        setAvailableBaseModels(modelNames);
      } else {
        // Modelos base comunes de Ollama
        setAvailableBaseModels([
          'llama2', 'llama2:13b', 'llama2:70b',
          'mistral', 'mistral:7b', 'mistral:instruct',
          'codellama', 'codellama:13b', 'codellama:34b',
          'vicuna', 'vicuna:13b', 'vicuna:33b',
          'orca-mini', 'orca-mini:13b',
          'neural-chat', 'starling-lm'
        ]);
      }
    } catch (err) {
      console.error('Error cargando modelos base:', err);
      // Fallback a modelos comunes
      setAvailableBaseModels([
        'llama2', 'llama2:13b', 'mistral', 'codellama', 'vicuna'
      ]);
    }
  };

  const loadOllamaModels = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getOllamaModels();
      
      // Función para formatear un modelo
      const formatModel = (model: any): OllamaModelResponse => ({
        id: model.id,
        name: model.name || 'Sin nombre',
        display_name: model.display_name || model.name || 'Sin nombre',
        base_model: model.base_model || 'Desconocido',
        size: model.size || 'Desconocido',
        modified_at: model.modified_at || new Date().toISOString(),
        digest: model.digest || 'N/A',
        system_prompt: model.system_prompt || '',
        temperature: model.temperature || 0.7,
        num_ctx: model.num_ctx || 2048,
        custom_template: model.custom_template || '',
        modelfile_content: model.modelfile_content || '',
        created_at: model.created_at || new Date().toISOString(),
        status: model.status || 'active'
      });
      
      // Verificar si la respuesta tiene la estructura esperada
      if (response.data) {
        let models: OllamaModelResponse[] = [];
        
        // Caso 1: Los modelos están en response.data.models
        if ('models' in response.data && Array.isArray(response.data.models)) {
          models = (response.data.models as any[]).map(formatModel);
          console.log('Modelos formateados (formato con .models):', models);
        } 
        // Caso 2: Los modelos están directamente en response.data (array)
        else if (Array.isArray(response.data)) {
          models = (response.data as any[]).map(formatModel);
          console.log('Modelos formateados (formato directo):', models);
        }
        // Caso 3: La respuesta es un objeto con una propiedad que es un array
        else {
          // Buscar cualquier propiedad que sea un array
          const arrayKey = Object.keys(response.data).find(
            key => Array.isArray((response.data as any)[key])
          );
          
          if (arrayKey) {
            models = ((response.data as any)[arrayKey] as any[]).map(formatModel);
            console.log(`Modelos formateados (encontrados en propiedad '${arrayKey}'):`, models);
          } else {
            console.warn('No se pudo encontrar un array de modelos en la respuesta:', response.data);
          }
        }
        
        setModels(models);
      } else {
        console.warn('La respuesta de la API no contiene datos:', response);
        setModels([]);
      }
    } catch (err) {
      console.error('Error al cargar modelos de Ollama:', err);
      setError('Error cargando modelos de Ollama');
      setModels([]);
    } finally {
      setLoading(false);
    }
  };


  const handleCreateModel = async () => {
    if (!formData.name.trim() || !formData.system_prompt.trim()) {
      setError('El nombre y el prompt del sistema son obligatorios');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const modelData = {
        name: formData.name,
        base_model: formData.base_model,
        system_prompt: formData.system_prompt,
        temperature: formData.temperature,
        num_ctx: formData.num_ctx,
        custom_template: formData.custom_template || undefined
      };

      const response = await apiClient.createOllamaModel(modelData);
      
      if (response.data) {
        setSuccess(`Modelo "${formData.name}" creado exitosamente`);
        setShowCreateModal(false);
        resetForm();
        await loadOllamaModels();
      } else {
        setError(response.error || 'Error creando el modelo');
      }
    } catch (err) {
      setError('Error creando el modelo de Ollama');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      base_model: 'llama3.2:3b',
      system_prompt: 'Eres un asistente útil y amigable.',
      temperature: 0.7,
      num_ctx: 2048,
      custom_template: ''
    });
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const handleUpdateModel = async (modelId: string) => {
    if (!formData.name.trim() || !formData.system_prompt.trim()) {
      setError('El nombre y el prompt del sistema son obligatorios');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const modelData = {
        name: formData.name,
        base_model: formData.base_model,
        system_prompt: formData.system_prompt,
        temperature: formData.temperature,
        num_ctx: formData.num_ctx,
        custom_template: formData.custom_template || undefined
      };

      const response = await apiClient.updateOllamaModel(modelId, modelData);
      
      if (response.data) {
        setSuccess(`Modelo "${formData.name}" actualizado exitosamente`);
        setShowEditModal(false);
        setSelectedModel(null);
        resetForm();
        await loadOllamaModels();
      } else {
        setError(response.error || 'Error actualizando el modelo');
      }
    } catch (err) {
      setError('Error actualizando el modelo de Ollama');
    } finally {
      setLoading(false);
    }
  };

  const populateEditForm = (model: any) => {
    setFormData({
      name: model.display_name || model.name,
      base_model: model.base_model,
      system_prompt: model.system_prompt,
      temperature: model.temperature,
      num_ctx: model.num_ctx,
      custom_template: model.custom_template || ''
    });
  };

  if (authLoading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <BrandLoader size="md" label="Cargando..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Acceso no autorizado</h2>
          <p className="text-gray-600">Debes iniciar sesión para acceder a esta funcionalidad.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      {showChat && selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">
                Chat con {selectedModel.display_name || selectedModel.name}
              </h2>
              <button
                onClick={() => setShowChat(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <div className="flex-1 overflow-auto">
              <OllamaChat 
                agentId={selectedModel.id}
                agentName={selectedModel.display_name || selectedModel.name}
                modelName={selectedModel.name}
                onBack={() => setShowChat(false)}
              />
            </div>
          </div>
        </div>
      )}


      {/* Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
          <span className="text-red-700">{error}</span>
          <button onClick={clearMessages} className="ml-auto text-red-500 hover:text-red-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
          <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
          <span className="text-green-700">{success}</span>
          <button onClick={clearMessages} className="ml-auto text-green-500 hover:text-green-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Models List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Modelos Disponibles</h2>
            <p className="text-gray-600 mt-1">Modelos de Ollama instalados en tu sistema</p>
          </div>
          <Button
            onClick={() => { setShowCreateModal(true); clearMessages(); }}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Crear modelo
          </Button>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <BrandLoader size="md" label="Cargando modelos..." />
            </div>
          ) : models.length === 0 ? (
            <div className="text-center py-12">
              <Cpu className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No hay modelos disponibles</h3>
              <p className="text-gray-600 mb-6">Crea tu primer modelo personalizado de Ollama</p>
              <Button
                onClick={() => { setShowCreateModal(true); clearMessages(); }}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Crear primer modelo
              </Button>
            </div>
          ) : (
            <div className="grid gap-4">
              {Array.isArray(models) && models.map((model, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-primary transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{model.name}</h3>
                      <p className="text-sm text-gray-600">Modelo base: {model.base_model}</p>
                      <p className="text-sm text-gray-500 mt-1">Tamaño: {model.size || 'Desconocido'}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                    <span className="px-3 py-1 text-xs bg-primary/10 text-primary rounded-full">
                      Ollama
                    </span>
                    <button
                      onClick={() => navigate(`/dashboard/agents/${model.id}`)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Ver detalles y configurar"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Model Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 flex items-center">
                <Cpu className="h-6 w-6 mr-2 text-primary" />
                Crear Modelo Ollama
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  resetForm();
                  clearMessages();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Nombre del modelo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre del modelo *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="mi-modelo-personalizado"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Usa solo letras minúsculas, números y guiones
                </p>
              </div>

              {/* Modelo base */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modelo base
                </label>
                <select
                  value={formData.base_model}
                  onChange={(e) => setFormData({ ...formData, base_model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  {availableBaseModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              {/* Prompt del sistema */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt del sistema *
                </label>
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  rows={4}
                  placeholder="Define la personalidad y comportamiento del modelo..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              {/* Configuración avanzada */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperatura ({formData.temperature})
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Conservador</span>
                    <span>Creativo</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contexto (tokens)
                  </label>
                  <input
                    type="number"
                    value={formData.num_ctx}
                    onChange={(e) => setFormData({ ...formData, num_ctx: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    min="512"
                    max="8192"
                    step="512"
                  />
                </div>
              </div>

              {/* Template personalizado */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template personalizado (opcional)
                </label>
                <textarea
                  value={formData.custom_template}
                  onChange={(e) => setFormData({ ...formData, custom_template: e.target.value })}
                  rows={3}
                  placeholder="Template personalizado para el formato de respuesta..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  resetForm();
                  clearMessages();
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateModel}
                disabled={loading || !formData.name.trim() || !formData.system_prompt.trim()}
                className="flex items-center px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <BrandLoader size="sm" className="mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Crear Modelo
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Edit Modal */}
      {showEditModal && selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 flex items-center">
                <Edit className="h-6 w-6 mr-2 text-green-600" />
                Editar Modelo: {selectedModel.display_name || selectedModel.name}
              </h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedModel(null);
                  resetForm();
                }}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
                <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            )}

            {success && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                <span className="text-green-700">{success}</span>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre del Modelo *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Ej: Mi Asistente Personalizado"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modelo Base
                </label>
                <select
                  value={formData.base_model}
                  onChange={(e) => setFormData({ ...formData, base_model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  {availableBaseModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt del Sistema *
                </label>
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Define la personalidad y comportamiento del modelo..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperatura ({formData.temperature})
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Conservador</span>
                    <span>Creativo</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contexto (tokens)
                  </label>
                  <input
                    type="number"
                    min="512"
                    max="8192"
                    step="512"
                    value={formData.num_ctx}
                    onChange={(e) => setFormData({ ...formData, num_ctx: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template Personalizado (Opcional)
                </label>
                <textarea
                  value={formData.custom_template}
                  onChange={(e) => setFormData({ ...formData, custom_template: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Template personalizado para el formato de respuesta..."
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedModel(null);
                  resetForm();
                  clearMessages();
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => handleUpdateModel(selectedModel.id)}
                disabled={loading || !formData.name.trim() || !formData.system_prompt.trim()}
                className="flex items-center px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <BrandLoader size="sm" className="mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Actualizar Modelo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Modal */}
      {showChat && selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-4xl h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">
                Chat con {selectedModel.name}
              </h3>
              <button
                onClick={() => setShowChat(false)}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <OllamaChat 
                agentId={selectedModel.id}
                agentName={selectedModel.name}
                modelName={selectedModel.base_model || 'Ollama Model'}
                onBack={() => setShowChat(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OllamaModelManager;