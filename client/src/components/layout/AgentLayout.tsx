import { useNavigate } from 'react-router-dom';
import { ChevronLeft, User } from 'lucide-react';
import { cn } from '../../lib/utils';

interface AgentLayoutProps {
  children: React.ReactNode;
  title: string;
  showBackButton?: boolean;
  className?: string;
  headerActions?: React.ReactNode;
  headerCenter?: React.ReactNode;
  headerRight?: React.ReactNode;
}

// Gradient background component similar to AuthLayout
const GradientBackground = () => (
  <div className="fixed inset-0 z-0 overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
    {/* Top right gradient */}
    <div className="absolute top-0 -right-1/4 w-3/4 h-3/4 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full filter blur-[180px] opacity-90" />
    
    {/* Bottom left gradient */}
    <div className="absolute -bottom-1/4 -left-1/4 w-3/4 h-3/4 bg-gradient-to-tr from-purple-100 to-purple-200 rounded-full filter blur-[200px] opacity-90" />
    
    {/* Center gradient */}
    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-gradient-to-r from-pink-100 to-pink-200 rounded-full filter blur-[220px] opacity-100" />
    
    {/* Subtle overlay */}
    <div className="absolute inset-0 bg-white/30 backdrop-blur-[1px]" />
  </div>
);

export function AgentLayout({
  children,
  title,
  showBackButton = true,
  className,
  headerActions,
  headerCenter,
  headerRight,
}: AgentLayoutProps) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col relative">
      <GradientBackground />
      
      {/* Header */}
      <header className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              {showBackButton && (
                <button
                  onClick={() => navigate(-1)}
                  className="p-2 rounded-full bg-white/70 hover:bg-white transition-colors shadow-sm"
                >
                  <ChevronLeft className="h-5 w-5 text-gray-700" />
                </button>
              )}
              <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
            </div>
            <div className="flex-1 flex items-center justify-center">
              {headerCenter || headerActions}
            </div>
            <div className="flex items-center gap-3">
              {headerRight}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className={cn("flex-grow relative z-10 py-8", className)}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          {children}
        </div>
      </main>
    </div>
  );
}
