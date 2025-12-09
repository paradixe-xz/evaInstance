import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import { API_ENDPOINTS, DEFAULT_HEADERS } from '../config/api';

// Create axios instance with base config
const api: AxiosInstance = axios.create({
  baseURL: '', // We're using full URLs in API_ENDPOINTS
  headers: DEFAULT_HEADERS,
  withCredentials: true, // Important for cookies if using HTTP-only cookies
});

// Request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(API_ENDPOINTS.AUTH.REFRESH, {
            refresh_token: refreshToken
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          if (refresh_token) {
            localStorage.setItem('refresh_token', refresh_token);
          }

          // Update the Authorization header
          originalRequest.headers.Authorization = `Bearer ${access_token}`;

          // Retry the original request
          return api(originalRequest);
        }
      } catch (err) {
        // If refresh fails, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  login: async (email: string, password: string) => {
    try {
      const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, {
        email,
        password,
      });

      console.log('Login response:', response.data); // Debug log

      if (!response.data || !response.data.access_token) {
        throw new Error('No se recibió un token de acceso válido');
      }

      const { access_token, refresh_token, user } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      // Store user data in localStorage
      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      }

      return user;
    } catch (error) {
      throw error;
    }
  },

  signup: async (name: string, email: string, password: string, company?: string) => {
    try {
      const response = await api.post(API_ENDPOINTS.AUTH.SIGNUP, {
        name,
        email,
        password,
        company,
      });

      const { access_token, refresh_token, user } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }

      return user;
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post(API_ENDPOINTS.AUTH.LOGOUT);
    } finally {
      // Clear tokens regardless of the API call result
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await api.get(API_ENDPOINTS.AUTH.ME);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

export const chatService = {
  getUsers: async (params?: { limit?: number; offset?: number; active_only?: boolean }) => {
    try {
      const response = await api.get(API_ENDPOINTS.CHAT.USERS, { params });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getChatHistory: async (phoneNumber: string, params?: { limit?: number; offset?: number }) => {
    try {
      const response = await api.get(API_ENDPOINTS.CHAT.HISTORY, {
        params: { phone_number: phoneNumber, ...params }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getActiveSessions: async (limit: number = 20) => {
    try {
      const response = await api.get(API_ENDPOINTS.CHAT.ACTIVE_SESSIONS, { params: { limit } });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  sendMessage: async (phoneNumber: string, message: string) => {
    try {
      const response = await api.post(API_ENDPOINTS.CHAT.SEND_MESSAGE, {
        phone_number: phoneNumber,
        message
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  updateUserAiStatus: async (userId: number, paused: boolean) => {
    try {
      const response = await api.patch(API_ENDPOINTS.CHAT.USER_AI_STATUS(userId), {
        ai_paused: paused
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

export default api;
