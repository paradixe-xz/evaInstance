import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import type { LoginRequest } from '../../services/api';
import { Input } from '../ui/input';
import { Button } from '../ui/button';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToSignup?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSwitchToSignup }) => {
  const { login, isLoading } = useAuth();
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.email || !formData.password) {
      setError('Por favor, completa todos los campos');
      return;
    }

    const result = await login(formData);
    
    if (result.success) {
      onSuccess?.();
    } else {
      setError(result.error || 'Error al iniciar sesión');
    }
  };

  return (
    <div className="w-full">
      <div>
        <div className="text-center mb-8">
          <div className="mx-auto h-14 w-14 bg-gradient-to-br from-green-300 to-green-500 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
            <span className="text-white font-bold text-2xl">E</span>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Bienvenido a Eva</h2>
          <p className="mt-2 text-slate-500">Inicia sesión en tu cuenta</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-700">
            Email
          </label>
          <div className="mt-1">
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="tu@empresa.com"
              disabled={isLoading}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <div className="text-sm">
              <a href="#" className="font-medium text-primary hover:text-green-600 text-sm">
                ¿Olvidaste tu contraseña?
              </a>
            </div>
          </div>
          <div className="mt-1">
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              disabled={isLoading}
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <div>
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full h-11"
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </div>

        {onSwitchToSignup && (
          <div className="text-center">
            <span className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={onSwitchToSignup}
                className="font-medium text-primary hover:text-green-600"
              >
                Regístrate
              </button>
            </span>
          </div>
        )}
      </form>
    </div>
  );
};

export default LoginForm;