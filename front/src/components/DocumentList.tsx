import React, { useState } from 'react';
import { 
  File, 
  Trash2, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  FileText
} from 'lucide-react';
import { apiClient } from '../services/api';

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

interface ProcessingStatus {
  document_id: number;
  status: string;
  total_chunks: number;
  processed_chunks: number;
  error_message?: string;
  progress_percentage: number;
}

interface DocumentListProps {
  agentId: number;
  documents: KnowledgeDocument[];
  onDocumentDelete: (documentId: number) => void;
  onDocumentReindex: (documentId: number) => void;
  onRefresh: () => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  agentId,
  documents,
  onDocumentDelete,
  onDocumentReindex,
  onRefresh,
}) => {
  const [loadingStates, setLoadingStates] = useState<Record<number, boolean>>({});

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completado';
      case 'processing':
        return 'Procesando';
      case 'failed':
        return 'Error';
      case 'uploading':
        return 'Subiendo';
      default:
        return status;
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return <FileText className="w-5 h-5 text-red-500" />;
      case 'docx':
        return <FileText className="w-5 h-5 text-blue-500" />;
      case 'txt':
      case 'md':
        return <FileText className="w-5 h-5 text-gray-500" />;
      case 'json':
        return <FileText className="w-5 h-5 text-green-500" />;
      default:
        return <File className="w-5 h-5 text-gray-400" />;
    }
  };

  const handleDelete = async (documentId: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este documento?')) {
      return;
    }

    setLoadingStates(prev => ({ ...prev, [documentId]: true }));
    
    try {
      const response = await apiClient.deleteDocument(agentId, documentId);
      if (response.error) {
        alert(`Error al eliminar: ${response.error}`);
      } else {
        onDocumentDelete(documentId);
      }
    } catch {
      alert('Error al eliminar el documento');
    } finally {
      setLoadingStates(prev => ({ ...prev, [documentId]: false }));
    }
  };

  const handleReindex = async (documentId: number) => {
    setLoadingStates(prev => ({ ...prev, [documentId]: true }));
    
    try {
      const response = await apiClient.reindexDocument(agentId, documentId);
      if (response.error) {
        alert(`Error al reindexar: ${response.error}`);
      } else {
        onDocumentReindex(documentId);
        // Refresh the list to get updated status
        onRefresh();
      }
    } catch {
      alert('Error al reindexar el documento');
    } finally {
      setLoadingStates(prev => ({ ...prev, [documentId]: false }));
    }
  };



  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <File className="mx-auto w-12 h-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-700 mb-2">
          No hay documentos
        </h3>
        <p className="text-gray-500">
          Sube tu primer documento para comenzar a construir la base de conocimiento.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-700">
          Documentos ({documents.length})
        </h3>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      <div className="space-y-3">
        {documents.map((document) => {
          const isLoading = loadingStates[document.id];
          
          return (
            <div
              key={document.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  {getFileTypeIcon(document.file_type)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900 truncate">
                        {document.title || document.original_filename}
                      </h4>
                      {getStatusIcon(document.status)}
                    </div>
                    
                    <div className="text-sm text-gray-500 space-y-1">
                      <p>{document.original_filename}</p>
                      <div className="flex items-center gap-4">
                        <span>{formatFileSize(document.file_size)}</span>
                        <span>{document.file_type.toUpperCase()}</span>
                        <span>{formatDate(document.created_at)}</span>
                      </div>
                      
                      {document.status === 'processing' && (
                        <div className="mt-2">
                          <div className="flex justify-between text-xs mb-1">
                            <span>Procesando chunks...</span>
                            <span>{document.processed_chunks}/{document.total_chunks}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                              style={{ 
                                width: `${document.total_chunks > 0 
                                  ? (document.processed_chunks / document.total_chunks) * 100 
                                  : 0}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      )}
                      
                      {document.status === 'completed' && (
                        <p className="text-green-600">
                          ✓ {document.total_chunks} chunks procesados
                        </p>
                      )}
                      
                      {document.status === 'failed' && document.error_message && (
                        <p className="text-red-600 text-xs">
                          Error: {document.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <span className={`
                    px-2 py-1 text-xs font-medium rounded-full
                    ${document.status === 'completed' 
                      ? 'bg-green-100 text-green-800' 
                      : document.status === 'processing'
                      ? 'bg-yellow-100 text-yellow-800'
                      : document.status === 'failed'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                    }
                  `}>
                    {getStatusText(document.status)}
                  </span>

                  {document.status === 'completed' && (
                    <button
                      onClick={() => handleReindex(document.id)}
                      disabled={isLoading}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Reindexar documento"
                    >
                      <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                  )}

                  <button
                    onClick={() => handleDelete(document.id)}
                    disabled={isLoading}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    title="Eliminar documento"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DocumentList;