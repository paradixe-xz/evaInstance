import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../contexts/AuthContext';

// Reutilizamos el mismo fondo de AuthLayout
const GradientBackground = () => (
  <div className="fixed inset-0 z-0 overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
    {/* Top right gradient - stronger blue tint */}
    <div className="absolute top-0 -right-1/4 w-3/4 h-3/4 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full filter blur-[180px] opacity-90" />
    
    {/* Bottom left gradient - stronger purple tint */}
    <div className="absolute -bottom-1/4 -left-1/4 w-3/4 h-3/4 bg-gradient-to-tr from-purple-100 to-purple-200 rounded-full filter blur-[200px] opacity-90" />
    
    {/* Center gradient - stronger pink tint */}
    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-gradient-to-r from-pink-100 to-pink-200 rounded-full filter blur-[220px] opacity-100" />
    
    {/* Subtle overlay to blend the gradients */}
    <div className="absolute inset-0 bg-white/30 backdrop-blur-[1px]" />
    
    {/* Subtle pattern */}
    <div className="absolute inset-0 bg-[radial-gradient(#00000008_1px,transparent_1px)] [background-size:20px_20px]" />
  </div>
);

interface MainLayoutProps {
  children: ReactNode;
  onLogout: () => void;
}

export function MainLayout({ children, onLogout }: MainLayoutProps) {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen w-full flex bg-gray-50">
      <GradientBackground />
      
      {/* Sidebar */}
      <div className="sticky top-0 z-10 h-screen">
        <Sidebar 
          onLogout={onLogout}
          userName={user?.name}
          userEmail={user?.email}
        />
      </div>
      
      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 overflow-y-auto p-6 relative z-10">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}