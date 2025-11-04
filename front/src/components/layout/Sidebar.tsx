import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  LogOut,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  activeItem?: string;
  onItemClick?: (item: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeItem = 'dashboard', onItemClick }) => {
  const { logout } = useAuth();

  const items = [
    { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, to: '/dashboard' },
    { key: 'agents', label: 'Agentes', icon: Users, to: '/dashboard/agents' },
    { key: 'knowledge', label: 'Conocimiento', icon: BookOpen, to: '/dashboard/knowledge' },
  ];

  const handleClick = (key: string, to: string) => {
    if (onItemClick) onItemClick(key);
  };

  return (
    <aside className="h-full w-[240px] bg-white border-r border-gray-200">
      <div className="px-4 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">EVA</h2>
      </div>

      <nav className="p-2 space-y-1">
        {items.map(({ key, label, icon: Icon, to }) => (
          <NavLink
            key={key}
            to={to}
            end={to === '/dashboard'}
            onClick={() => handleClick(key, to)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-[10px] text-sm transition-colors ${
                isActive || activeItem === key
                  ? 'bg-primary/10 text-primary'
                  : 'text-gray-700 hover:bg-gray-100'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto p-4 border-t border-gray-200">
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-[10px] text-sm text-red-600 hover:bg-red-50"
        >
          <LogOut className="h-5 w-5" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;