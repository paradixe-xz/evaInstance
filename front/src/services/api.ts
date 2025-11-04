const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Basic interfaces
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
  first_name: string;
  last_name: string;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: number;
  name: string;
  description?: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  target_audience?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  created_at: string;
  updated_at: string;
  user_id: number;
}

export interface Agent {
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
  knowledge_base_enabled?: boolean;
  voice_enabled?: boolean;
  personality_traits?: Record<string, any>;
  response_style?: string;
  language_preferences?: string[];
  custom_instructions?: string;
  interaction_history?: Record<string, any>;
  performance_metrics?: Record<string, any>;
  last_interaction?: string;
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
  id: number;
  name: string;
  display_name: string;
  base_model: string;
  size?: string;
  modified_at: string | null;
  digest?: string;
  system_prompt: string;
  temperature: number;
  num_ctx: number;
  custom_template?: string | null;
  modelfile_content?: string | null;
  created_at: string | null;
  status: string;
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
  processing_documents: number;
  failed_documents: number;
  total_size_bytes: number;
  avg_chunk_size: number;
}

export interface RAGResponse {
  response: string;
  sources: KnowledgeSearchResult[];
  search_query: string;
  total_sources: number;
}

// API Client Class
export class ApiClient {
  private token: string | null = null;
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || data.message || 'Request failed',
        };
      }

      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<ApiResponse<{ access_token: string; user: User }>> {
    const response = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (response.data?.access_token) {
      this.token = response.data.access_token;
      localStorage.setItem('token', this.token);
    }

    return response;
  }

  async signup(userData: SignupRequest): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('token');
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/me');
  }

  // Campaign methods
  async getCampaigns(): Promise<ApiResponse<Campaign[]>> {
    return this.request<Campaign[]>('/campaigns');
  }

  async createCampaign(campaign: Omit<Campaign, 'id' | 'created_at' | 'updated_at' | 'user_id'>): Promise<ApiResponse<Campaign>> {
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

  // Agent methods
  async getAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>('/agents');
  }

  async createAgent(agent: Omit<Agent, 'id' | 'created_at' | 'updated_at' | 'user_id'>): Promise<ApiResponse<Agent>> {
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

  // Ollama methods
  async getOllamaModels(): Promise<ApiResponse<{ models: OllamaModelResponse[] } | OllamaModelResponse[]>> {
    return this.request<{ models: OllamaModelResponse[] } | OllamaModelResponse[]>('/agents/ollama/models');
  }

  async createOllamaModel(model: OllamaModelCreate): Promise<ApiResponse<any>> {
    return this.request<any>('/agents/ollama/create', {
      method: 'POST',
      body: JSON.stringify(model),
    });
  }

  async deleteOllamaModel(name: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/agents/ollama/delete/${name}`, {
      method: 'DELETE',
    });
  }

  // Knowledge Base methods
  async uploadDocument(agentId: number, file: File): Promise<ApiResponse<KnowledgeDocument>> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseURL}/knowledge/${agentId}/upload`;
    const headers: HeadersInit = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || data.message || 'Upload failed',
        };
      }

      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  async getDocuments(agentId: number): Promise<ApiResponse<KnowledgeDocument[]>> {
    return this.request<KnowledgeDocument[]>(`/knowledge/${agentId}/documents`);
  }

  async deleteDocument(agentId: number, documentId: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/knowledge/${agentId}/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async getProcessingStatus(agentId: number, documentId: number): Promise<ApiResponse<ProcessingStatus>> {
    return this.request<ProcessingStatus>(`/knowledge/${agentId}/documents/${documentId}/status`);
  }

  async reindexDocument(agentId: number, documentId: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/knowledge/${agentId}/documents/${documentId}/reindex`, {
      method: 'POST',
    });
  }

  async searchKnowledge(agentId: number, query: string, limit: number = 10): Promise<ApiResponse<KnowledgeSearchResponse>> {
    return this.request<KnowledgeSearchResponse>(`/knowledge/${agentId}/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  }

  async getKnowledgeStats(agentId: number): Promise<ApiResponse<KnowledgeStats>> {
    return this.request<KnowledgeStats>(`/knowledge/${agentId}/stats`);
  }

  async ragQuery(agentId: number, query: string): Promise<ApiResponse<RAGResponse>> {
    return this.request<RAGResponse>(`/knowledge/${agentId}/rag`, {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  // Utility methods
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('token', token);
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
    
    console.log('🚀 Frontend API Call:', {
      agentId,
      message,
      conversationHistory,
      body,
      url: `${this.baseURL}/agents/ollama/${agentId}/chat/public`
    });
    
    const result = await this.request<any>(`/agents/ollama/${agentId}/chat/public`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    console.log('📥 Frontend API Response:', result);
    return result;
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

  async getOllamaBaseModels(): Promise<ApiResponse<{ success: boolean; base_models: any[]; count: number }>> {
    return this.request<{ success: boolean; base_models: any[]; count: number }>('/agents/ollama/base-models');
  }

  async updateOllamaModel(modelId: string, modelData: OllamaModelCreate): Promise<ApiResponse<any>> {
    return this.request<any>(`/agents/ollama/${modelId}`, {
      method: 'PUT',
      body: JSON.stringify(modelData),
    });
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  // WhatsApp methods
  async getWhatsAppConversations(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/whatsapp/conversations');
  }

  async sendWhatsAppMessage(phone: string, message: string): Promise<ApiResponse<any>> {
    return this.request<any>('/whatsapp/send', {
      method: 'POST',
      body: JSON.stringify({ phone, message }),
    });
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();

export default apiClient;