import React, { useState, useRef } from 'react';
import { Upload } from 'lucide-react';
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

interface DocumentUploadProps {
  agentId: number;
  onUploadSuccess: (document: KnowledgeDocument) => void;
  onUploadError: (error: string) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  agentId,
  onUploadSuccess,
  onUploadError,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const supportedTypes = [
    '.pdf',
    '.txt',
    '.docx',
    '.md',
    '.json'
  ];

  const maxFileSize = 50 * 1024 * 1024; // 50MB

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize) {
      return `El archivo es demasiado grande. Máximo permitido: ${maxFileSize / (1024 * 1024)}MB`;
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!supportedTypes.includes(fileExtension)) {
      return `Tipo de archivo no soportado. Tipos permitidos: ${supportedTypes.join(', ')}`;
    }

    return null;
  };

  const handleFileUpload = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      onUploadError(validationError);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await apiClient.uploadDocument(agentId, file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.error) {
        onUploadError(response.error);
      } else if (response.data) {
        onUploadSuccess(response.data);
      }
    } catch (error) {
      onUploadError(error instanceof Error ? error.message : 'Error al subir el archivo');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
          ${isDragging 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${isUploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={supportedTypes.join(',')}
          onChange={handleFileSelect}
          disabled={isUploading}
        />

        {isUploading ? (
          <div className="space-y-4">
            <div className="animate-spin mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Subiendo documento...</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500">{uploadProgress}%</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className="mx-auto w-12 h-12 text-gray-400" />
            <div className="space-y-2">
              <p className="text-lg font-medium text-gray-700">
                Arrastra un documento aquí o haz clic para seleccionar
              </p>
              <p className="text-sm text-gray-500">
                Tipos soportados: {supportedTypes.join(', ')}
              </p>
              <p className="text-xs text-gray-400">
                Tamaño máximo: {maxFileSize / (1024 * 1024)}MB
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;