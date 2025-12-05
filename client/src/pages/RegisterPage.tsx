import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AuthLayout } from '../components/layout/AuthLayout';
import { authService } from '../services/api';
import { toast } from 'sonner';


export function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    company: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Call the registration API
      await authService.signup(
        formData.name,
        formData.email,
        formData.password,
        formData.company
      );
      
      // Show success message
      toast.success('¡Registro exitoso! Redirigiendo...');
      
      // Redirect to login page after a short delay
      setTimeout(() => {
        navigate('/login');
      }, 1500);
      
    } catch (error: any) {
      console.error('Error en el registro:', error);
      
      // Show error message from the API or a generic one
      const errorMessage = error.response?.data?.detail || 'Error en el registro. Por favor, inténtalo de nuevo.';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <AuthLayout>
      <div className="w-full">
        <div className="text-left mb-8">
          <div className="bg-gray-100 p-4 rounded-full inline-flex mb-6">
            <UserPlus className="h-8 w-8 text-gray-700" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Crea tu cuenta</h1>
          <p className="text-gray-600 text-base">Completa el formulario para registrarte</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo
            </label>
            <Input
              id="name"
              name="name"
              type="text"
              placeholder="Juan Pérez"
              value={formData.name}
              onChange={handleChange}
              className="w-full h-11 text-sm border-gray-200"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Correo electrónico
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="tu@email.com"
              value={formData.email}
              onChange={handleChange}
              className="w-full h-11 text-sm border-gray-200"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              className="w-full h-11 text-sm border-gray-200"
              required
            />
          </div>
          
          <div className="mb-8">
            <div className="flex justify-between items-center mb-1">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirmar contraseña
              </label>
            </div>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder="••••••••"
              value={formData.confirmPassword}
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
            {isLoading ? 'Creando cuenta...' : 'Registrarse'}
          </Button>
          
          <div className="text-center text-sm text-gray-600 pt-6">
            ¿Ya tienes una cuenta?{' '}
            <Link to="/login" className="font-medium text-primary hover:underline transition-colors">
              Inicia sesión
            </Link>
          </div>
        </form>
      </div>
    </AuthLayout>
  );
}
