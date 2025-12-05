import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Settings, LogOut, ChevronRight, ChevronLeft, MessageSquare } from 'lucide-react';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { useState } from 'react';

interface SidebarProps {
  onLogout: () => void;
  userName?: string;
  userEmail?: string;
}

const menuItems = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { name: 'WhatsApp', icon: MessageSquare, href: '/dashboard/whatsapp' },
  { name: 'Agentes', icon: Users, href: '/dashboard/agentes' },
  { name: 'Configuración', icon: Settings, href: '/dashboard/configuracion' },
];

export function Sidebar({ onLogout, userName = 'Usuario', userEmail = 'usuario@ejemplo.com' }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div
      className={cn(
        "flex flex-col h-screen transition-all duration-300 ease-in-out",
        isCollapsed ? "w-20" : "w-72"
      )}
    >
      <div className={cn("flex items-center p-4", isCollapsed ? "justify-center" : "justify-between")}>
        {!isCollapsed ? (
          <div className="flex items-center">
            <span className="text-xl font-bold text-primary">EVA</span>
          </div>
        ) : (
          <div className="w-6"></div> // Empty div to maintain spacing
        )}
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            "h-8 w-8 bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white/70 transition-all",
            isCollapsed ? "mx-auto" : "ml-auto"
          )}
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
        {isCollapsed && <div className="w-6"></div>} {/* Empty div to maintain spacing */}
      </div>

      <nav className="flex-1 overflow-y-auto p-2 mt-2">
        <ul className="space-y-1">
          {menuItems.map((item) => (
            <li key={item.href} className={cn("px-2", isCollapsed && "flex justify-center")}>
              <Link
                to={item.href}
                className={cn(
                  "flex items-center py-2.5 text-sm font-medium rounded-lg transition-colors",
                  isCollapsed ? "justify-center w-10 h-10" : "w-full px-3",
                  location.pathname.startsWith(item.href) && item.href !== '/dashboard'
                    ? "bg-primary/10 text-primary"
                    : location.pathname === item.href
                      ? "bg-primary/10 text-primary"
                      : "text-gray-700 hover:bg-gray-100/50"
                )}
                title={isCollapsed ? item.name : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!isCollapsed && <span className="ml-3 truncate">{item.name}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {!isCollapsed && (
        <div className="p-4 mt-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium">
              {userName.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{userName}</p>
              <p className="text-xs text-gray-500 truncate">{userEmail}</p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={onLogout}
            className="w-full justify-center text-gray-700 bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white/70 transition-all"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Cerrar sesión
          </Button>
        </div>
      )}
      {isCollapsed && (
        <div className="p-2 border-t border-gray-100 flex justify-center">
          <Button
            variant="outline"
            size="icon"
            onClick={onLogout}
            className="bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white/70 transition-all"
            title="Cerrar sesión"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      )}
    </div>
  );
}