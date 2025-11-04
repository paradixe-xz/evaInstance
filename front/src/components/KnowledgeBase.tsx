import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Upload, 
  Search, 
  BarChart3, 
  AlertCircle, 
  CheckCircle,
  RefreshCw,
  Database
} from 'lucide-react';
import { apiClient } from '../services/api';

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
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import KnowledgeSearch from './KnowledgeSearch';

interface KnowledgeDocument {
  id: number;
  agent_id: number;
  original_filename: string;
  stored_filename: string;
  file_type: string;
  file_size: number;
  file_hash: string;
  title?: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  total_chunks: number;
  processed_chunks: number;
  error_message?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  processing_documents: number;
  failed_documents: number;
  total_size_bytes: number;
  avg_chunk_size: number;
}

interface KnowledgeBaseProps {
  agent: Agent;
}

type TabType = 'upload' | 'documents' | 'search' | 'stats';

const KnowledgeBase: React.FC<KnowledgeBaseProps> = ({ agent }) => {
  const [activeTab, setActiveTab] = useState<TabType>('documents');
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const tabs = [
    { id: 'documents' as TabType, label: 'Documentos', icon: BookOpen },
    { id: 'upload' as TabType, label: 'Subir', icon: Upload },
    { id: 'search' as TabType, label: 'Buscar', icon: Search },
    { id: 'stats' as TabType, label: 'Estadísticas', icon: BarChart3 },
  ];

  useEffect(() => {
    loadData();
  }, [agent.id]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [documentsResponse, statsResponse] = await Promise.all([
        apiClient.getDocuments(agent.id),
        apiClient.getKnowledgeStats(agent.id)
      ]);

      if (documentsResponse.error) {
        setError(documentsResponse.error);
      } else if (documentsResponse.data) {
        setDocuments(documentsResponse.data);
      }

      if (statsResponse.data) {
        setStats(statsResponse.data);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Error al cargar datos');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadSuccess = (document: KnowledgeDocument) => {
    setDocuments(prev => [document, ...prev]);
    setSuccessMessage(`Documento "${document.original_filename}" subido correctamente`);
    setActiveTab('documents');
    loadData(); // Refresh stats
    
    // Clear success message after 5 seconds
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  const handleUploadError = (error: string) => {
    setError(error);
    setTimeout(() => setError(null), 5000);
  };

  const handleDocumentDelete = (documentId: number) => {
    setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    loadData(); // Refresh stats
  };

  const handleDocumentReindex = () => {
    // The document list will handle the reindexing
    // We just need to refresh the data
    setTimeout(() => loadData(), 1000);
  };

  const clearMessages = () => {
    setError(null);
    setSuccessMessage(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        <span className="ml-3 text-gray-600">Cargando base de conocimiento...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-600" />
              Base de Conocimiento
            </h1>
            <p className="text-gray-600 mt-1">
              Gestiona los documentos y conocimiento del agente "{agent.name}"
            </p>
          </div>
          
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Actualizar
          </button>
        </div>

        {/* Quick Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600">{stats.total_documents}</div>
              <div className="text-sm text-blue-700">Documentos</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">{stats.total_chunks}</div>
              <div className="text-sm text-green-700">Chunks</div>
            </div>
            <div className="bg-primary/5 rounded-lg p-4">
              <div className="text-2xl font-bold text-primary">
                {(stats.total_size_bytes / (1024 * 1024)).toFixed(1)}MB
              </div>
              <div className="text-sm text-primary">Tamaño total</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-600">{stats.processing_documents}</div>
              <div className="text-sm text-yellow-700">Procesando</div>
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      {(error || successMessage) && (
        <div className="space-y-2">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="font-medium text-red-800">Error</h4>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
              <button
                onClick={clearMessages}
                className="text-red-400 hover:text-red-600"
              >
                ×
              </button>
            </div>
          )}
          
          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="font-medium text-green-800">Éxito</h4>
                <p className="text-green-700 text-sm mt-1">{successMessage}</p>
              </div>
              <button
                onClick={clearMessages}
                className="text-green-400 hover:text-green-600"
              >
                ×
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'documents' && (
            <DocumentList
              agentId={agent.id}
              documents={documents}
              onDocumentDelete={handleDocumentDelete}
              onDocumentReindex={handleDocumentReindex}
              onRefresh={loadData}
            />
          )}

          {activeTab === 'upload' && (
            <div className="max-w-2xl mx-auto">
              <DocumentUpload
                agentId={agent.id}
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </div>
          )}

          {activeTab === 'search' && (
            <div className="max-w-4xl mx-auto">
              <KnowledgeSearch agentId={agent.id} />
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="max-w-4xl mx-auto">
              <KnowledgeStatsView stats={stats} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface KnowledgeStatsViewProps {
  stats: KnowledgeStats | null;
}

const KnowledgeStatsView: React.FC<KnowledgeStatsViewProps> = ({ stats }) => {
  if (!stats) {
    return (
      <div className="text-center py-8">
        <BarChart3 className="mx-auto w-12 h-12 text-gray-400 mb-4" />
        <p className="text-gray-500">No hay estadísticas disponibles</p>
      </div>
    );
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900">Estadísticas de la Base de Conocimiento</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100">Total de Documentos</p>
              <p className="text-3xl font-bold">{stats.total_documents}</p>
            </div>
            <BookOpen className="w-8 h-8 text-blue-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100">Total de Chunks</p>
              <p className="text-3xl font-bold">{stats.total_chunks}</p>
            </div>
            <Database className="w-8 h-8 text-green-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-primary/80 to-primary rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-primary/20">Tamaño Total</p>
              <p className="text-3xl font-bold">{formatBytes(stats.total_size_bytes)}</p>
            </div>
            <BarChart3 className="w-8 h-8 text-primary/30" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-100">Procesando</p>
              <p className="text-3xl font-bold">{stats.processing_documents}</p>
            </div>
            <RefreshCw className="w-8 h-8 text-yellow-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-red-500 to-red-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100">Con Errores</p>
              <p className="text-3xl font-bold">{stats.failed_documents}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-200" />
          </div>
        </div>


      </div>

      {stats.total_chunks > 0 && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h4 className="font-medium text-gray-900 mb-4">Información Adicional</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Promedio de chunks por documento:</span>
              <span className="ml-2 font-medium">
                {stats.total_documents > 0 ? (stats.total_chunks / stats.total_documents).toFixed(1) : '0'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Tamaño promedio por documento:</span>
              <span className="ml-2 font-medium">
                {stats.total_documents > 0 ? formatBytes(stats.total_size_bytes / stats.total_documents) : '0 Bytes'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;