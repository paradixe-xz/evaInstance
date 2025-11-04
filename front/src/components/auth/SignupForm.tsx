import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import type { SignupRequest } from '../../services/api';
import { Input } from '../ui/input';
import { Button } from '../ui/button';

interface SignupFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

const SignupForm: React.FC<SignupFormProps> = ({ onSuccess, onSwitchToLogin }) => {
  const { signup, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    company: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.firstName || !formData.lastName || !formData.email || !formData.password) {
      setError('Por favor, completa todos los campos obligatorios');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (formData.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    const signupData: SignupRequest = {
      first_name: formData.firstName,
      last_name: formData.lastName,
      email: formData.email,
      password: formData.password,
    };

    const result = await signup(signupData);

    if (result.success) {
      onSuccess?.();
    } else {
      setError(result.error || 'Error al crear la cuenta');
    }
  };

  return (
    <div className="w-full">
      <div>
        <div className="text-center mb-8">
          <div className="mx-auto h-14 w-14 bg-gradient-to-br from-green-300 to-green-500 rounded-2xl flex items-center justify-center mb-4 shadow-sm">
            <span className="text-white font-bold text-2xl">E</span>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Crear cuenta en Eva</h2>
          <p className="mt-2 text-slate-500">Únete a la plataforma de agentes de IA</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label htmlFor="firstName" className="block text-sm font-medium text-slate-700">
              Nombre
            </label>
            <div className="mt-1">
              <Input
                id="firstName"
                name="firstName"
                type="text"
                autoComplete="given-name"
                required
                value={formData.firstName}
                onChange={handleChange}
                placeholder="Nombre"
                disabled={isLoading}
              />
            </div>
          </div>

          <div>
            <label htmlFor="lastName" className="block text-sm font-medium text-slate-700">
              Apellido
            </label>
            <div className="mt-1">
              <Input
                id="lastName"
                name="lastName"
                type="text"
                autoComplete="family-name"
                required
                value={formData.lastName}
                onChange={handleChange}
                placeholder="Apellido"
                disabled={isLoading}
              />
            </div>
          </div>
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-700">
            Correo electrónico
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
          <label htmlFor="company" className="block text-sm font-medium text-slate-700">
            Empresa (opcional)
          </label>
          <div className="mt-1">
            <Input
              id="company"
              name="company"
              type="text"
              autoComplete="organization"
              value={formData.company}
              onChange={handleChange}
              placeholder="Empresa (opcional)"
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Contraseña
            </label>
            <div className="mt-1">
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700">
              Confirmar contraseña
            </label>
            <div className="mt-1">
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <div>
          <Button type="submit" disabled={isLoading} className="w-full h-11">
            {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
          </Button>
        </div>

        {onSwitchToLogin && (
          <div className="mt-6 text-center text-sm text-slate-500">
            <span>¿Ya tienes una cuenta? </span>
            <button
              type="button"
              onClick={onSwitchToLogin}
              className="font-medium text-primary hover:text-green-600"
            >
              Inicia sesión
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

export default SignupForm;