import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { ArrowUp, ArrowDown, Search, Bell, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Datos de ejemplo para los gráficos
const activityData = [
  { name: 'Ene', value: 4000 },
  { name: 'Feb', value: 3000 },
  { name: 'Mar', value: 2000 },
  { name: 'Abr', value: 2780 },
  { name: 'May', value: 1890 },
  { name: 'Jun', value: 2390 },
  { name: 'Jul', value: 3490 },
];

const conversationData = [
  { name: 'Lun', value: 12 },
  { name: 'Mar', value: 19 },
  { name: 'Mié', value: 15 },
  { name: 'Jue', value: 11 },
  { name: 'Vie', value: 8 },
  { name: 'Sáb', value: 5 },
  { name: 'Dom', value: 2 },
];

const recentConversations = [
  { id: 1, name: 'Juan Pérez', lastMessage: 'Hola, necesito ayuda con mi pedido', time: '2 min', status: 'online' },
  { id: 2, name: 'María García', lastMessage: '¿Tienen stock del producto X?', time: '1h', status: 'offline' },
  { id: 3, name: 'Carlos López', lastMessage: 'Gracias por su ayuda', time: '3h', status: 'online' },
  { id: 4, name: 'Ana Martínez', lastMessage: '¿Cuál es el tiempo de envío?', time: '5h', status: 'offline' },
];

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <MainLayout onLogout={handleLogout}>
      <div className="w-full">
        {/* Header con breadcrumbs y acciones */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center text-sm text-gray-500">
              <span>Inicio</span>
              <ChevronRight className="h-4 w-4 mx-2" />
              <span className="text-primary">Dashboard</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar..."
                className="pl-10 pr-4 py-2 rounded-lg border border-gray-200 bg-white/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent"
              />
            </div>
            <Button variant="outline" size="icon" className="bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white/70">
              <Bell className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Bienvenido, {user?.name?.split(' ')[0] || 'Usuario'}</h2>
          <p className="text-gray-600">Aquí está el resumen de tu actividad</p>
        </div>

        {/* Tarjetas de métricas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-500">Clientes Totales</CardDescription>
              <CardTitle className="text-2xl font-bold">2,420</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-green-500">
                <ArrowUp className="h-4 w-4 mr-1" />
                <span>12% desde el mes pasado</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-500">Conversaciones Activas</CardDescription>
              <CardTitle className="text-2xl font-bold">189</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-green-500">
                <ArrowUp className="h-4 w-4 mr-1" />
                <span>8% desde ayer</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-500">Tasa de Respuesta</CardDescription>
              <CardTitle className="text-2xl font-bold">86%</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-red-500">
                <ArrowDown className="h-4 w-4 mr-1" />
                <span>2% desde ayer</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-gray-500">Satisfacción del Cliente</CardDescription>
              <CardTitle className="text-2xl font-bold">4.8/5</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm text-green-500">
                <ArrowUp className="h-4 w-4 mr-1" />
                <span>0.2 desde la semana pasada</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader>
              <CardTitle>Actividad de mensajes</CardTitle>
              <CardDescription>Resumen de los últimos 7 días</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={activityData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <CartesianGrid strokeDasharray="3 3" className="stroke-gray-100" />
                  <Tooltip />
                  <Area type="monotone" dataKey="value" stroke="#6366f1" fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader>
              <CardTitle>Conversaciones por día</CardTitle>
              <CardDescription>Distribución de la última semana</CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={conversationData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-gray-100" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Conversaciones recientes */}
        <div className="flex flex-col">
          <Card className="bg-white/50 backdrop-blur-sm border border-white/70 shadow-sm">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Conversaciones recientes</CardTitle>
                  <CardDescription>Últimas interacciones con los clientes</CardDescription>
                </div>
                <Button variant="outline" className="bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white/70">
                  Ver todo
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentConversations.map((conversation) => (
                  <div key={conversation.id} className="flex items-center justify-between p-3 hover:bg-gray-50/50 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
                          {conversation.name.charAt(0)}
                        </div>
                        <span className={`absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full ${conversation.status === 'online' ? 'bg-green-500' : 'bg-gray-300'} ring-2 ring-white`}></span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{conversation.name}</p>
                        <p className="text-sm text-gray-500">{conversation.lastMessage}</p>
                      </div>
                    </div>
                    <span className="text-sm text-gray-500">{conversation.time}</span>
                  </div>
                ))}
              </div>
              
              {/* Botón de más conversaciones */}
              <div className="mt-6">
                <Button variant="outline" className="w-full bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white/70">
                  Ver más conversaciones
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}