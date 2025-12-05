// API base URL - update this with your actual backend URL
export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    SIGNUP: `${API_BASE_URL}/auth/signup`,
    ME: `${API_BASE_URL}/auth/me`,
    REFRESH: `${API_BASE_URL}/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
  },
  AGENTS: {
    ROOT: `${API_BASE_URL}/agents`,
    OLLAMA: {
      CREATE: `${API_BASE_URL}/agents/ollama/create`,
      CHAT: (id: number) => `${API_BASE_URL}/agents/ollama/${id}/chat`,
    },
  },
};

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};
