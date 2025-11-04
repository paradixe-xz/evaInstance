import React, { useState } from 'react';
import { Search, FileText, AlertCircle } from 'lucide-react';
import { apiClient } from '../services/api';

interface KnowledgeSearchResult {
  chunk_id: number;
  content: string;
  similarity_score: number;
  document_filename: string;
  document_title?: string;
  page_number?: number;
  metadata?: Record<string, any>;
}

interface KnowledgeSearchResponse {
  results: KnowledgeSearchResult[];
  total_results: number;
  search_time_ms: number;
  query: string;
}

interface KnowledgeSearchProps {
  agentId: number;
}

const KnowledgeSearch: React.FC<KnowledgeSearchProps> = ({ agentId }) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const response = await apiClient.searchKnowledge(agentId, query.trim(), 10);
      
      if (response.error) {
        setError(response.error);
        setSearchResults(null);
      } else if (response.data) {
        setSearchResults(response.data);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Error al buscar');
      setSearchResults(null);
    } finally {
      setIsSearching(false);
    }
  };

  const highlightText = (text: string, query: string): string => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');
  };

  const formatSimilarityScore = (score: number): string => {
    return `${(score * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar en la base de conocimiento..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isSearching}
          />
        </div>
        
        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          {isSearching ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              Buscando...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Buscar
            </>
          )}
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-red-800">Error en la búsqueda</h4>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              Resultados de búsqueda
            </h3>
            <div className="text-sm text-gray-500">
              {searchResults.total_results} resultados en {searchResults.search_time_ms}ms
            </div>
          </div>

          {searchResults.results.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="mx-auto w-12 h-12 text-gray-400 mb-4" />
              <h4 className="text-lg font-medium text-gray-700 mb-2">
                No se encontraron resultados
              </h4>
              <p className="text-gray-500">
                Intenta con diferentes términos de búsqueda o verifica que hay documentos procesados.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {searchResults.results.map((result, index) => (
                <SearchResultCard
                  key={`${result.chunk_id}-${index}`}
                  result={result}
                  query={query}
                  highlightText={highlightText}
                  formatSimilarityScore={formatSimilarityScore}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface SearchResultCardProps {
  result: KnowledgeSearchResult;
  query: string;
  highlightText: (text: string, query: string) => string;
  formatSimilarityScore: (score: number) => string;
}

const SearchResultCard: React.FC<SearchResultCardProps> = ({
  result,
  query,
  highlightText,
  formatSimilarityScore,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const maxLength = 300;
  const shouldTruncate = result.content.length > maxLength;
  const displayContent = shouldTruncate && !isExpanded 
    ? result.content.substring(0, maxLength) + '...'
    : result.content;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-4 h-4 text-gray-500" />
            <h4 className="font-medium text-gray-900 truncate">
              {result.document_title || result.document_filename}
            </h4>
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>{result.document_filename}</span>
            {result.page_number && (
              <span>Página {result.page_number}</span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          <span className="text-xs text-gray-500">
            Relevancia: {formatSimilarityScore(result.similarity_score)}
          </span>
          <div 
            className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden"
            title={`Relevancia: ${formatSimilarityScore(result.similarity_score)}`}
          >
            <div 
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${result.similarity_score * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="text-sm text-gray-700 leading-relaxed">
        <div 
          dangerouslySetInnerHTML={{ 
            __html: highlightText(displayContent, query) 
          }}
        />
        
        {shouldTruncate && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {isExpanded ? 'Ver menos' : 'Ver más'}
          </button>
        )}
      </div>

      {result.metadata && Object.keys(result.metadata).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <details className="text-xs text-gray-500">
            <summary className="cursor-pointer hover:text-gray-700">
              Metadatos
            </summary>
            <pre className="mt-2 bg-gray-50 p-2 rounded text-xs overflow-x-auto">
              {JSON.stringify(result.metadata, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default KnowledgeSearch;