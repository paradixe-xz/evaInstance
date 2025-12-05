import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { LogIn } from 'lucide-react';
import { AuthLayout } from '../components/layout/AuthLayout';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

export function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsLoading(true);
      
      // Call the login API through AuthContext
      const success = await login(formData.email, formData.password);
      
      if (success) {
        // Show success message
        toast.success('¡Bienvenido de nuevo!');
        
        // Get the redirect location or default to '/dashboard'
        const from = (location.state as any)?.from?.pathname || '/dashboard';
        
        // Redirect to the intended location or dashboard
        navigate(from, { replace: true });
      }
      
    } catch (error: any) {
      console.error('Error en el inicio de sesión:', error);
      
      // Show error message from the API or a generic one
      const errorMessage = error.response?.data?.detail || 'Error en el inicio de sesión. Por favor, verifica tus credenciales.';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full">
        <div className="text-left mb-8">
          <div className="bg-gray-100 p-4 rounded-full inline-flex mb-6">
            <LogIn className="h-8 w-8 text-gray-700" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Bienvenido a EVA</h1>
          <p className="text-gray-600 text-base">Por favor, inicia sesión o regístrate a continuación.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Correo electrónico
            </label>
            <Input
              id="email"
              type="email"
              placeholder="tu@email.com"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full h-11 text-sm border-gray-200"
              required
            />
          </div>
          
          <div className="mb-6">
            <div className="flex justify-between items-center mb-1">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <Link to="/forgot-password" className="text-xs text-gray-500 hover:text-primary transition-colors">
                ¿Olvidaste tu contraseña?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full h-11 text-sm border-gray-200"
              required
            />
          </div>
          
          <Button 
            type="submit" 
            className="w-full bg-primary hover:bg-gray-800 h-12 text-base font-medium text-white rounded-lg mt-2 transition-colors"
            disabled={isLoading}
          >
            {isLoading ? 'Iniciando sesión...' : 'Continuar con correo'}
          </Button>
          
          
          <div className="text-center text-sm text-gray-600 pt-6">
            ¿No tienes una cuenta?{' '}
            <Link to="/register" className="font-medium text-primary hover:underline transition-colors">
              Regístrate
            </Link>
          </div>
        </form>
      </div>
    </AuthLayout>
  );
}
