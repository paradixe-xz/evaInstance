/**
 * API client for Eva backend communication
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
  company?: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
  company?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Campaign {
  id: number;
  name: string;
  description?: string;
  slug: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  type: 'calls' | 'whatsapp' | 'mixed';
  total_calls: number;
  total_whatsapp_messages: number;
  success_rate: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: number;
  name: string;
  description?: string;
  agent_type: 'calls' | 'whatsapp';
  status: 'active' | 'inactive' | 'training';
  is_active: boolean;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
  personality_traits?: Record<string, any>;
  conversation_style?: Record<string, any>;
  voice_settings?: Record<string, any>;
  behavior_config?: Record<string, any>;
  performance_metrics?: Record<string, any>;
  training_data?: Record<string, any>;
  creator_id: number;
  campaign_id?: number;
  // Ollama-specific fields
  is_ollama_model: boolean;
  ollama_model_name?: string;
  base_model?: string;
  num_ctx?: number;
  modelfile_content?: string;
  custom_template?: string;
  ollama_parameters?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface OllamaModelCreate {
  name: string;
  base_model: string;
  system_prompt: string;
  temperature?: number;
  num_ctx?: number;
  custom_template?: string;
}

export interface OllamaModelResponse {
  agent: Agent;
  model_created: boolean;
  message: string;
}

// Knowledge Base interfaces
export interface KnowledgeDocument {
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

export interface KnowledgeChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  token_count: number;
  start_char?: number;
  end_char?: number;
  page_number?: number;
  embedding_model?: string;
  embedding_dimension?: number;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSearchResponse {
  results: KnowledgeSearchResult[];
  total_results: number;
  search_time_ms: number;
  query: string;
}

export interface KnowledgeSearchResult {
  chunk_id: number;
  content: string;
  similarity_score: number;
  document_filename: string;
  document_title?: string;
  page_number?: number;
  metadata?: Record<string, any>;
}

export interface ProcessingStatus {
  document_id: number;
  status: string;
  total_chunks: number;
  processed_chunks: number;
  error_message?: string;
  progress_percentage: number;
}

export interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  total_size_bytes: number;
  processing_documents: number;
  failed_documents: number;
  embedding_model: string;
}

export interface RAGResponse {
  ai_response: string;
  knowledge_used: boolean;
  sources: KnowledgeSearchResult[];
  knowledge_count: number;
}

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('eva_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: HeadersInit = {
      ...options.headers,
    };

    // Only set Content-Type if not using FormData
    if (!(options.body instanceof FormData)) {
      (headers as Record<string, string>)['Content-Type'] = 'application/json';
    }

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<ApiResponse<{ access_token: string; user: User }>> {
    return this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }).then(response => {
      if (response.data) {
        this.token = response.data.access_token;
        localStorage.setItem('eva_token', this.token!);
      }
      return response;
    });
  }

  async signup(userData: SignupRequest): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/me');
  }

  async logout(): Promise<void> {
    this.token = null;
    localStorage.removeItem('eva_token');
    await this.request('/auth/logout', { method: 'POST' });
  }

  // Campaign methods
  async getCampaigns(): Promise<ApiResponse<Campaign[]>> {
    return this.request<Campaign[]>('/campaigns');
  }

  async getCampaign(id: number): Promise<ApiResponse<Campaign>> {
    return this.request<Campaign>(`/campaigns/${id}`);
  }

  async createCampaign(campaign: Partial<Campaign>): Promise<ApiResponse<Campaign>> {
    return this.request<Campaign>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(campaign),
    });
  }

  async updateCampaign(id: number, campaign: Partial<Campaign>): Promise<ApiResponse<Campaign>> {
    return this.request<Campaign>(`/campaigns/${id}`, {
      method: 'PUT',
      body: JSON.stringify(campaign),
    });
  }

  async deleteCampaign(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/campaigns/${id}`, {
      method: 'DELETE',
    });
  }

  async startCampaign(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/campaigns/${id}/start`, {
      method: 'POST',
    });
  }

  async stopCampaign(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/campaigns/${id}/stop`, {
      method: 'POST',
    });
  }

  // Agent methods
  async getAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>('/agents');
  }

  async getAgent(id: number): Promise<ApiResponse<Agent>> {
    return this.request<Agent>(`/agents/${id}`);
  }

  async createAgent(agent: Partial<Agent>): Promise<ApiResponse<Agent>> {
    return this.request<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(agent),
    });
  }

  async updateAgent(id: number, agent: Partial<Agent>): Promise<ApiResponse<Agent>> {
    return this.request<Agent>(`/agents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(agent),
    });
  }

  async deleteAgent(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/agents/${id}`, {
      method: 'DELETE',
    });
  }

  async activateAgent(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/agents/${id}/activate`, {
      method: 'POST',
    });
  }

  async deactivateAgent(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/agents/${id}/deactivate`, {
      method: 'POST',
    });
  }

  async testAgent(id: number, message: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/agents/${id}/test?message=${encodeURIComponent(message)}`);
  }

  // Ollama-specific methods
  async createOllamaModel(modelData: OllamaModelCreate): Promise<ApiResponse<any>> {
    return this.request<any>('/agents/ollama/create', {
      method: 'POST',
      body: JSON.stringify(modelData),
    });
  }

  async getOllamaBaseModels(): Promise<ApiResponse<{ success: boolean; models: any[]; count: number }>> {
    return this.request<{ success: boolean; models: any[]; count: number }>('/agents/ollama/models');
  }

  async getOllamaModels(): Promise<ApiResponse<{ success: boolean; models: any[]; count: number }>> {
    return this.request<{ success: boolean; models: any[]; count: number }>('/agents/ollama/models');
  }

  async getOllamaAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>('/agents/ollama');
  }

  async getAgentModelfile(id: number): Promise<ApiResponse<{ modelfile_content: string }>> {
    return this.request<{ modelfile_content: string }>(`/agents/${id}/modelfile`);
  }

  async updateOllamaModel(modelId: string, modelData: OllamaModelCreate): Promise<ApiResponse<any>> {
    return this.request<any>(`/agents/ollama/${modelId}`, {
      method: 'PUT',
      body: JSON.stringify(modelData),
    });
  }

  async chatWithOllamaModel(
    agentId: number, 
    message: string, 
    conversationHistory?: Array<{role: string, content: string}>
  ): Promise<ApiResponse<any>> {
    const body = {
      message: message,
      conversation_history: conversationHistory || []
    };
    
    return this.request<any>(`/agents/ollama/${agentId}/chat/public`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
  }

  // Knowledge Base methods
  async uploadDocument(agentId: number, file: File): Promise<ApiResponse<KnowledgeDocument>> {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.request<KnowledgeDocument>(`/knowledge/agents/${agentId}/upload`, {
      method: 'POST',
      body: formData,
    });
  }

  async getDocuments(agentId: number): Promise<ApiResponse<KnowledgeDocument[]>> {
    return this.request<KnowledgeDocument[]>(`/knowledge/agents/${agentId}/documents`);
  }

  async getDocument(documentId: number): Promise<ApiResponse<KnowledgeDocument>> {
    return this.request<KnowledgeDocument>(`/knowledge/documents/${documentId}`);
  }

  async deleteDocument(documentId: number): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/knowledge/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async searchKnowledge(agentId: number, query: string, limit?: number): Promise<ApiResponse<KnowledgeSearchResponse>> {
    const params = new URLSearchParams({ query });
    if (limit) params.append('limit', limit.toString());
    
    return this.request<KnowledgeSearchResponse>(`/knowledge/agents/${agentId}/search?${params}`);
  }

  async reindexDocument(documentId: number): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/knowledge/documents/${documentId}/reindex`, {
      method: 'POST',
    });
  }

  async getProcessingStatus(documentId: number): Promise<ApiResponse<ProcessingStatus>> {
    return this.request<ProcessingStatus>(`/knowledge/documents/${documentId}/status`);
  }

  async getKnowledgeStats(agentId: number): Promise<ApiResponse<KnowledgeStats>> {
    return this.request<KnowledgeStats>(`/knowledge/agents/${agentId}/stats`);
  }

  async chatWithKnowledge(agentId: number, message: string, conversationHistory?: any[]): Promise<ApiResponse<RAGResponse>> {
    const body = {
      message: message,
      conversation_history: conversationHistory || []
    };
    
    return this.request<RAGResponse>(`/agents/ollama/${agentId}/chat/knowledge`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // Utility methods
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('eva_token', token);
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();


export default apiClient;