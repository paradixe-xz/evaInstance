import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { apiClient } from '../services/api';
import type { User, LoginRequest, SignupRequest } from '../services/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<{ success: boolean; error?: string }>;
  signup: (userData: SignupRequest) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && apiClient.isAuthenticated();

  useEffect(() => {
    const initAuth = async () => {
      if (apiClient.isAuthenticated()) {
        await refreshUser();
      } else {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    try {
      const response = await apiClient.login(credentials);
      
      if (response.error) {
        setIsLoading(false);
        return { success: false, error: response.error };
      }

      if (response.data) {
        setUser(response.data.user);
        setIsLoading(false);
        return { success: true };
      }

      setIsLoading(false);
      return { success: false, error: 'Login failed' };
    } catch (error) {
      setIsLoading(false);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Login failed' 
      };
    }
  };

  const signup = async (userData: SignupRequest): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true);
    try {
      const response = await apiClient.signup(userData);
      
      if (response.error) {
        setIsLoading(false);
        return { success: false, error: response.error };
      }

      if (response.data) {
        // After successful signup, automatically log in
        const loginResult = await login({ 
          email: userData.email, 
          password: userData.password 
        });
        return loginResult;
      }

      setIsLoading(false);
      return { success: false, error: 'Signup failed' };
    } catch (error) {
      setIsLoading(false);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Signup failed' 
      };
    }
  };

  const logout = () => {
    apiClient.logout();
    setUser(null);
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const response = await apiClient.getCurrentUser();
      
      if (response.data) {
        setUser(response.data);
      } else {
        // Token might be invalid, logout
        logout();
      }
    } catch (error) {
      // Token might be invalid, logout
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    signup,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;