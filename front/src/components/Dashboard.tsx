import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Plus,
  Phone,
  MessageCircle,
  Bot,
  TrendingUp,
  ArrowUpRight,
  AlertCircle
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { apiClient } from '../services/api';
import type { Campaign, Agent } from '../services/api';

const Dashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('Este mes');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [agentsActive, setAgentsActive] = useState<number | null>(null);
  const [loadingData, setLoadingData] = useState<boolean>(false);

  useEffect(() => {
    const load = async () => {
      setLoadingData(true);
      try {
        const [campaignRes, agentsRes] = await Promise.all([
          apiClient.getCampaigns(),
          apiClient.getAgents()
        ]);
        setCampaigns(campaignRes?.data || []);
        const agents = agentsRes?.data || [];
        const activeCount = (agents as Agent[]).filter((a) => a.is_active).length;
        setAgentsActive(activeCount);
      } catch (err) {
        setCampaigns([]);
        setAgentsActive(null);
      } finally {
        setLoadingData(false);
      }
    };
    load();
  }, []);
  


  // Stats cards data (usar '-' cuando no hay datos reales)
  const stats = [
    {
      title: 'Llamadas totales',
      value: '-',
      change: '-',
      trend: 'up',
      icon: <Phone className="h-5 w-5 text-primary" />
    },
    {
      title: 'Chats de WhatsApp',
      value: '-',
      change: '-',
      trend: 'up',
      icon: <MessageCircle className="h-5 w-5 text-blue-500" />
    },
    {
      title: 'Agentes activos',
      value: agentsActive === null ? '-' : String(agentsActive),
      change: '-',
      trend: 'up',
      icon: <Bot className="h-5 w-5 text-primary" />
    },
    {
      title: 'Tasa de éxito',
      value: '-',
      change: '-',
      trend: 'up',
      icon: <TrendingUp className="h-5 w-5 text-yellow-500" />
    }
  ];

  return (
    <div className="space-y-6 mt-6">
      {/* Controles superiores */}
      <div className="flex justify-end">
        <div className="flex items-center space-x-2">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="h-11 rounded-[10px] border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-offset-2"
          >
            <option value="Hoy">Hoy</option>
            <option value="Ayer">Ayer</option>
            <option value="Esta semana">Esta semana</option>
            <option value="Este mes">Este mes</option>
            <option value="Este año">Este año</option>
          </select>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Nueva campaña
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className="h-5 w-5">
                {stat.icon}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground flex items-center">
                {stat.trend === 'up' ? (
                  <ArrowUpRight className="h-3 w-3 text-primary mr-1" />
                ) : (
                  <ArrowUpRight className="h-3 w-3 text-red-500 mr-1 rotate-180" />
                )}
                {stat.change} desde el mes pasado
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Campaigns Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Tus campañas</CardTitle>
              <CardDescription>
                Resumen de rendimiento de tus campañas activas
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" className="ml-auto gap-1">
              Ver todo
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b text-sm text-muted-foreground [&>th]:h-12 [&>th]:text-left [&>th]:font-medium [&>th:first-child]:pl-4 [&>th:last-child]:pr-4">
                  <th>Campaña</th>
                  <th>Estado</th>
                  <th>Llamadas</th>
                  <th>WhatsApp</th>
                  <th>Agentes</th>
                  <th>Éxito</th>
                  <th className="w-[100px]">Acciones</th>
                </tr>
              </thead>
              <tbody className="[&>tr:last-child]:border-0 [&>tr]:border-b">
                {campaigns.length === 0 ? (
                  <tr>
                    <td className="p-4 text-sm text-muted-foreground" colSpan={7}>
                      {loadingData ? 'Cargando...' : 'Sin campañas -'}
                    </td>
                  </tr>
                ) : (
                  campaigns.map((campaign) => (
                    <tr key={campaign.id} className="hover:bg-muted/50">
                      <td className="p-4 font-medium">{campaign.name}</td>
                      <td>
                        <div className="flex items-center">
                          <div className={`h-2 w-2 rounded-full mr-2 ${
                            campaign.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
                          }`} />
                          <span className="capitalize">
                            {campaign.status === 'active' ? 'Activo' : (campaign.status === 'paused' ? 'Pausado' : campaign.status)}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">-</td>
                      <td className="p-4">-</td>
                      <td className="p-4">-</td>
                      <td className="p-4">-</td>
                      <td className="p-4">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <ArrowUpRight className="h-4 w-4" />
                          <span className="sr-only">Ver detalles</span>
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="bg-primary/5 border-primary/10">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Acciones rápidas</CardTitle>
              <AlertCircle className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start">
              <Plus className="mr-2 h-4 w-4" />
              Crear nueva campaña
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Bot className="mr-2 h-4 w-4" />
              Agregar agente
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Settings className="mr-2 h-4 w-4" />
              Configuración
            </Button>
          </CardContent>
        </Card>

        <Card className="md:col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>Actividad reciente</CardTitle>
            <CardDescription>Últimas interacciones con los clientes</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Sin datos reales para actividad, mostramos '-' */}
            <p className="text-sm text-muted-foreground">Sin datos -</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;