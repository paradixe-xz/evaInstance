import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface AuthLayoutProps {
  children: ReactNode;
}

// High contrast gradient background with more vibrant colors
const GradientBackground = () => (
  <div className="fixed inset-0 z-10 overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
    {/* Top right gradient - stronger blue tint */}
    <div className="absolute top-0 -right-1/4 w-3/4 h-3/4 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full filter blur-[180px] opacity-90" />
    
    {/* Bottom left gradient - stronger purple tint */}
    <div className="absolute -bottom-1/4 -left-1/4 w-3/4 h-3/4 bg-gradient-to-tr from-purple-100 to-purple-200 rounded-full filter blur-[200px] opacity-90" />
    
    {/* Center gradient - stronger pink tint */}
    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-gradient-to-r from-pink-100 to-pink-200 rounded-full filter blur-[220px] opacity-100" />
    
    {/* Subtle overlay to blend the gradients */}
    <div className="absolute inset-0 bg-white/30 backdrop-blur-[1px]" />
  </div>
);

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col relative">
      <GradientBackground />
      {/* Header */}
      <header className="py-6 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="">
          <div className="flex justify-between items-center">
            <Link to="/" className="text-2xl font-bold text-gray-900">
              EVA
            </Link>
            <nav className="flex items-center space-x-4">
              <Link to="/login" className="text-gray-600 hover:text-primary text-sm font-medium transition-colors">
                Iniciar Sesión
              </Link>
              <Link 
                to="/register" 
                className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
              >
                Regístrate
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex items-center justify-center p-4 relative z-10">
        <div className="w-full max-w-[420px] bg-white/50 backdrop-blur-sm rounded-2xl p-8 shadow-sm border border-white/70">
          {children}
        </div>
      </main>
    </div>
  );
}
