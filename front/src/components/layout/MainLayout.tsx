import React, { useCallback, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Sidebar from './Sidebar';
import { Menu, X } from 'lucide-react';

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  const getActiveItem = useCallback(() => {
    const path = location.pathname;
    if (path.startsWith('/dashboard/agents/') || path === '/dashboard/agents') return 'agents';
    if (path.includes('/knowledge')) return 'knowledge';
    return 'dashboard';
  }, [location.pathname]);

  const handleNavigation = useCallback((item: string) => {
    if (item === 'logout') {
      logout();
      return;
    }
    setSidebarOpen(false);
    navigate(`/dashboard${item === 'dashboard' ? '' : `/${item}`}`);
  }, [navigate, logout]);

  if (location.pathname.startsWith('/dashboard/agents/')) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/30 z-20"
          onClick={toggleSidebar}
        ></div>
      )}

      {/* Sidebar fixed */}
      <div className={`fixed inset-y-0 left-0 transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-200 ease-in-out z-30 w-[240px]`}>
        <Sidebar 
          activeItem={getActiveItem()} 
          onItemClick={handleNavigation} 
        />
      </div>

      {/* Content wrapper offset by sidebar */}
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-[240px]">
        {/* Fixed header (hero) */}
        <header className="h-16 border-b border-gray-200 bg-white fixed top-0 left-0 right-0 lg:left-[240px] z-40">
          <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <button
              type="button"
              className="lg:hidden inline-flex items-center justify-center rounded-[10px] p-2 hover:bg-gray-100 text-gray-600"
              onClick={toggleSidebar}
            >
              <span className="sr-only">Abrir menú</span>
              {sidebarOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
            <div className="flex-1 flex justify-between items-center">
              <h1 className="text-lg font-semibold text-gray-900 ml-4 lg:ml-0">
                {getPageTitle(location.pathname)}
              </h1>
            </div>
          </div>
        </header>

        {/* Page content below header */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6 pt-16">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

const getPageTitle = (path: string): string => {
  if (path.includes('/agents')) return 'Agentes IA';
  if (path.includes('/knowledge')) return 'Base de Conocimiento';
  return 'Panel de Control';
};

export default MainLayout;