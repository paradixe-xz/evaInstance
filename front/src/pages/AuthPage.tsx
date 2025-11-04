import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import BrandLoader from '../components/ui/BrandLoader';

const AuthPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [isLogin, setIsLogin] = useState(true);

  // If user is already authenticated, redirect to dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <BrandLoader size="lg" />
          <h1 className="text-2xl font-bold text-foreground mt-6">Cargando...</h1>
        </div>
      </div>
    );
  }

  const handleAuthSuccess = () => {
    // Navigation will be handled by the Navigate component above
    // when isAuthenticated becomes true
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-background text-foreground">
      {/* Conditional layout based on current form */}
      {isLogin ? (
        <>
          {/* Left side - Login Form */}
          <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24 bg-card order-2 lg:order-1">
            <div className="mx-auto w-full max-w-sm lg:w-96">
              <LoginForm
                onSuccess={handleAuthSuccess}
                onSwitchToSignup={() => setIsLogin(false)}
              />
            </div>
          </div>
          
          {/* Right side - Brand Panel */}
          <div className="lg:h-64 lg:min-h-screen lg:sticky lg:top-0 lg:w-1/2 order-1 lg:order-2 rounded-b-3xl lg:rounded-b-none lg:rounded-l-3xl bg-background bg-grid-pattern">
            <div className="h-full flex items-center justify-center p-8">
              <div className="text-center">
                <h2 className="text-3xl font-bold mb-4">Bienvenido de nuevo</h2>
                <h3 className="text-muted-foreground">Inicia sesión para acceder a tu cuenta</h3>
              </div>
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Left side - Brand Panel */}
          <div className="lg:h-64 lg:min-h-screen lg:sticky lg:top-0 lg:w-1/2 order-1 rounded-b-3xl lg:rounded-b-none lg:rounded-r-3xl bg-background bg-grid-pattern">
            <div className="h-full flex items-center justify-center p-8">
              <div className="text-center">
                <h2 className="text-3xl font-bold mb-4">¡Bienvenido a EVA!</h2>
                <h3 className="text-muted-foreground">Crea tu cuenta para comenzar</h3>
              </div>
            </div>
          </div>
          
          {/* Right side - Signup Form */}
          <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24 bg-card order-2">
            <div className="mx-auto w-full max-w-sm lg:w-96">
              <SignupForm
                onSuccess={handleAuthSuccess}
                onSwitchToLogin={() => setIsLogin(true)}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AuthPage;