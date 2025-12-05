import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { Search, ChevronRight, Bot, Plus, Edit, StopCircle, Play, Filter, Eye } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { MainLayout } from '../components/layout/MainLayout';
import { cn } from '../lib/utils';
import api from '../services/api';
import { API_BASE_URL } from '../config/api';

type AIAgent = {
  id: number;
  name: string;
  description: string;
  model: string;
  status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  agent_type: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
};

const API_URL = API_BASE_URL;

export function AgentesPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  // Error state is declared but not used in the UI
  const [, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    let isMounted = true;

    const fetchAIAgents = async () => {
      try {
        setIsLoading(true);
        console.log('Fetching agents from API...');

        // Use the api instance which includes the auth interceptor
        const response = await api.get(`${API_URL}/agents/`);

        if (isMounted) {
          const data = response.data;
          console.log('Agents loaded:', data);
          setAgents(Array.isArray(data) ? data : []);
          setError(null);
        }
      } catch (error: any) {
        console.error('Error al cargar agentes de IA:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'No se pudieron cargar los agentes de IA';
        setError(errorMessage);

        if (error.response?.status === 401) {
          console.log('Not authenticated, redirecting to login...');
          logout();
          navigate('/login');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchAIAgents();

    return () => {
      isMounted = false;
    };
  }, [navigate, logout]);

  const filteredAgents = agents.filter(agent => {
    const matchesSearch =
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (agent.description && agent.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (agent.model && agent.model.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && agent.status === 'active') ||
      (statusFilter === 'inactive' && agent.status === 'inactive') ||
      (statusFilter === 'draft' && agent.status === 'draft');

    return matchesSearch && matchesStatus;
  });

  const toggleAgentStatus = async (agentId: number) => {
    try {
      const agent = agents.find(a => a.id === agentId);
      if (!agent) return;

      const newStatus = agent.status === 'active' ? 'inactive' : 'active';
      const response = await api.put(`${API_URL}/agents/${agentId}`, { status: newStatus });

      const updatedAgent = response.data;

      if (!updatedAgent) throw new Error('No se recibió respuesta del servidor');

      setAgents(agents.map(a =>
        a.id === agentId ? { ...a, ...updatedAgent } : a
      ));

      // toast.success(`Agente ${updatedAgent.is_active ? 'activado' : 'desactivado'} correctamente`);
    } catch (error) {
      console.error('Error al cambiar el estado del agente:', error);
      // toast.error('No se pudo actualizar el estado del agente');
    }
  };

  const handleCreateClick = () => {
    navigate('/dashboard/agentes/nuevo');
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
      toast.success('Has cerrado sesión correctamente');
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
      toast.error('No se pudo cerrar la sesión. Por favor, inténtalo de nuevo.');
    }
  };

  return (
    <MainLayout
      onLogout={handleLogout}
    >
      <div className="w-full space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Agentes de IA</h1>
            <div className="flex items-center text-sm text-gray-500 mt-1">
              <span>Inicio</span>
              <ChevronRight className="h-4 w-4 mx-2" />
              <span className="text-primary">Agentes de IA</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 z-10" />
                  <input
                    type="text"
                    placeholder="Buscar agentes..."
                    className="pl-10 pr-4 py-2 w-full sm:w-64 rounded-lg bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary/50 transition-all duration-200"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <div className="relative">
                  <div className="flex items-center">
                    <Filter className="h-4 w-4 text-gray-400 mr-2" />
                    <select
                      className="pl-2 pr-8 py-2 rounded-lg bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary/50 transition-all duration-200 appearance-none"
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="all">Todos los estados</option>
                      <option value="active">Activos</option>
                      <option value="inactive">Inactivos</option>
                      <option value="draft">Borradores</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <Button
              onClick={handleCreateClick}
              className="bg-black text-white hover:bg-gray-800"
            >
              <Plus className="mr-2 h-4 w-4" />
              Nuevo Agente
            </Button>
          </div>
        </div>

        <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="w-[200px] font-medium">Nombre</TableHead>
                    <TableHead>Descripción</TableHead>
                    <TableHead className="w-[150px]">Modelo</TableHead>
                    <TableHead className="w-[150px] text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow className="hover:bg-white/30">
                      <TableCell colSpan={4} className="h-64 text-center">
                        <div className="flex flex-col items-center justify-center space-y-4">
                          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
                          <p className="text-sm text-muted-foreground">Cargando agentes...</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : agents.length === 0 ? (
                    <TableRow className="hover:bg-white/30">
                      <TableCell colSpan={4} className="h-64 text-center">
                        <div className="flex flex-col items-center justify-center space-y-4">
                          <Bot className="h-12 w-12 text-muted-foreground/30" />
                          <div className="space-y-1">
                            <p className="font-medium">No hay agentes creados</p>
                            <p className="text-sm text-muted-foreground">Comienza creando tu primer agente</p>
                          </div>
                          <Button
                            onClick={handleCreateClick}
                            className="mt-2 bg-black text-white hover:bg-gray-800"
                          >
                            <Plus className="h-4 w-4 mr-2" />
                            Nuevo Agente
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : filteredAgents.length === 0 ? (
                    <TableRow className="hover:bg-white/30">
                      <TableCell colSpan={4} className="h-32 text-center">
                        <div className="flex flex-col items-center justify-center space-y-2">
                          <Search className="h-8 w-8 text-muted-foreground/30" />
                          <p className="text-muted-foreground">No se encontraron agentes que coincidan con tu búsqueda</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAgents.map((agent) => (
                      <TableRow key={agent.id} className="hover:bg-gray-50">
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <Bot className={`h-4 w-4 ${agent.is_active ? 'text-green-500' : 'text-gray-400'}`} />
                            <span className="font-medium">{agent.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-gray-600 max-w-[300px] truncate">
                          {agent.description}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {agent.model}
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-1">
                            <Button
                              asChild
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0 hover:bg-gray-200"
                              title="Ver/Editar"
                            >
                              <a href={`/dashboard/agentes/${agent.id}`} onClick={(e) => {
                                e.preventDefault();
                                console.log('Navigating to agent ID:', agent.id);
                                navigate(`/dashboard/agentes/${agent.id}`);
                              }}>
                                <Eye className="h-4 w-4" />
                              </a>
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}