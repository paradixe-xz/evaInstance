// API base URL - update this with your actual backend URL
export const API_BASE_URL = '/api/v1';

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
  CHAT: {
    USERS: `${API_BASE_URL}/chat/users`,
    HISTORY: `${API_BASE_URL}/chat/history`,
    ACTIVE_SESSIONS: `${API_BASE_URL}/chat/active-sessions`,
    SEND_MESSAGE: `${API_BASE_URL}/chat/message`,
    USER_AI_STATUS: (userId: number) => `${API_BASE_URL}/chat/user/${userId}/ai-status`,
    BULK_TEMPLATE: `${API_BASE_URL}/chat/bulk-template`,
  },
};

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};
