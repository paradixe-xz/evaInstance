import React, { useState } from 'react';
import { 
  Phone, 
  MessageCircle, 
  Bot, 
  Settings, 
  Plus, 
  Edit3, 
  TrendingUp,
  Clock,
  DollarSign,
  MoreVertical
} from 'lucide-react';

interface CampaignDetailProps {
  campaignId: string;
}

const CampaignDetail: React.FC<CampaignDetailProps> = ({ campaignId }) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Mock data - esto vendría del backend
  const campaign = {
    id: campaignId,
    name: 'Ventas Q1',
    status: 'active',
    description: 'Campaña de ventas para el primer trimestre del año',
    createdAt: '2024-01-15',
    stats: {
      totalCalls: 156,
      totalWhatsApp: 89,
      activeAgents: 3,
      successRate: 78,
      avgDuration: '4:32',
      totalCost: 245.50
    }
  };

  const agents = [
    {
      id: 'agent-1',
      name: 'Agente Ventas Pro',
      type: 'calls',
      status: 'active',
      calls: 89,
      successRate: 82,
      avgDuration: '5:12',
      lastActive: '2 min ago'
    },
    {
      id: 'agent-2',
      name: 'Asistente WhatsApp',
      type: 'whatsapp',
      status: 'active',
      messages: 156,
      responseTime: '30s',
      lastActive: '1 min ago'
    },
    {
      id: 'agent-3',
      name: 'Seguimiento Automático',
      type: 'calls',
      status: 'paused',
      calls: 34,
      successRate: 65,
      avgDuration: '3:45',
      lastActive: '1 hour ago'
    }
  ];

  const phoneNumbers = [
    {
      id: 'phone-1',
      number: '+1 (555) 123-4567',
      type: 'outbound',
      status: 'active',
      callsToday: 23,
      agent: 'Agente Ventas Pro'
    },
    {
      id: 'phone-2',
      number: '+1 (555) 987-6543',
      type: 'inbound',
      status: 'active',
      callsToday: 15,
      agent: 'Seguimiento Automático'
    }
  ];

  const whatsappNumbers = [
    {
      id: 'wa-1',
      number: '+1 (555) 111-2222',
      status: 'active',
      messagesTotal: 89,
      agent: 'Asistente WhatsApp',
      lastMessage: '5 min ago'
    }
  ];

  const tabs = [
    { id: 'overview', label: 'Resumen', icon: TrendingUp },
    { id: 'agents', label: 'Agentes', icon: Bot },
    { id: 'numbers', label: 'Números', icon: Phone },
    { id: 'whatsapp', label: 'WhatsApp', icon: MessageCircle },
    { id: 'settings', label: 'Configuración', icon: Settings }
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
            <p className="text-gray-600 mt-1">{campaign.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 text-sm rounded-full ${
              campaign.status === 'active' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {campaign.status === 'active' ? 'Activa' : 'Pausada'}
            </span>
            <button className="flex items-center px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
              <Settings className="h-4 w-4 mr-2" />
              Configurar
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">Llamadas</div>
              <Phone className="h-4 w-4 text-blue-500" />
            </div>
            <div className="text-2xl font-bold">{campaign.stats.totalCalls}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">WhatsApp</div>
              <MessageCircle className="h-4 w-4 text-green-500" />
            </div>
            <div className="text-2xl font-bold">{campaign.stats.totalWhatsApp}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">Agentes</div>
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="text-2xl font-bold">{campaign.stats.activeAgents}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">Éxito</div>
              <TrendingUp className="h-4 w-4 text-orange-500" />
            </div>
            <div className="text-2xl font-bold">{campaign.stats.successRate}%</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">Duración</div>
              <Clock className="h-4 w-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold">{campaign.stats.avgDuration}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">Costo</div>
              <DollarSign className="h-4 w-4 text-red-500" />
            </div>
            <div className="text-2xl font-bold">${campaign.stats.totalCost}</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-black text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Actividad reciente</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                  <Phone className="h-4 w-4 text-blue-600" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">Llamada completada exitosamente</div>
                  <div className="text-xs text-gray-500">Agente Ventas Pro • hace 2 minutos</div>
                </div>
              </div>
              <div className="flex items-center">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                  <MessageCircle className="h-4 w-4 text-green-600" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">Mensaje de WhatsApp respondido</div>
                  <div className="text-xs text-gray-500">Asistente WhatsApp • hace 5 minutos</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Agentes de IA</h3>
            <button className="flex items-center px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
              <Plus className="h-4 w-4 mr-2" />
              Nuevo agente
            </button>
          </div>

          <div className="grid gap-4">
            {agents.map((agent) => (
              <div key={agent.id} className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center mr-3">
                       <Bot className="h-5 w-5 text-primary" />
                     </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900">{agent.name}</h4>
                      <div className="flex items-center mt-1">
                        <span className={`px-2 py-1 text-xs rounded-full mr-2 ${
                          agent.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {agent.status === 'active' ? 'Activo' : 'Pausado'}
                        </span>
                        <span className="text-xs text-gray-500">{agent.type === 'calls' ? 'Llamadas' : 'WhatsApp'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 text-gray-400 hover:text-gray-600">
                      <Edit3 className="h-4 w-4" />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-gray-600">
                      <MoreVertical className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {agent.type === 'calls' ? (
                    <>
                      <div>
                        <div className="text-sm text-gray-600">Llamadas</div>
                        <div className="font-medium">{agent.calls}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Éxito</div>
                        <div className="font-medium">{agent.successRate}%</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Duración</div>
                        <div className="font-medium">{agent.avgDuration}</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div>
                        <div className="text-sm text-gray-600">Mensajes</div>
                        <div className="font-medium">{agent.messages}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Respuesta</div>
                        <div className="font-medium">{agent.responseTime}</div>
                      </div>
                    </>
                  )}
                  <div>
                    <div className="text-sm text-gray-600">Última actividad</div>
                    <div className="font-medium">{agent.lastActive}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'numbers' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Números de teléfono</h3>
            <button className="flex items-center px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
              <Plus className="h-4 w-4 mr-2" />
              Agregar número
            </button>
          </div>

          <div className="grid gap-4">
            {phoneNumbers.map((phone) => (
              <div key={phone.id} className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                      <Phone className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900">{phone.number}</h4>
                      <div className="flex items-center mt-1">
                        <span className={`px-2 py-1 text-xs rounded-full mr-2 ${
                          phone.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {phone.status === 'active' ? 'Activo' : 'Inactivo'}
                        </span>
                        <span className="text-xs text-gray-500">{phone.type === 'outbound' ? 'Saliente' : 'Entrante'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Llamadas hoy</div>
                    <div className="text-2xl font-bold">{phone.callsToday}</div>
                    <div className="text-xs text-gray-500">Agente: {phone.agent}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'whatsapp' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Números de WhatsApp</h3>
            <button className="flex items-center px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
              <Plus className="h-4 w-4 mr-2" />
              Agregar WhatsApp
            </button>
          </div>

          <div className="grid gap-4">
            {whatsappNumbers.map((whatsapp) => (
              <div key={whatsapp.id} className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                      <MessageCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900">{whatsapp.number}</h4>
                      <div className="flex items-center mt-1">
                        <span className={`px-2 py-1 text-xs rounded-full mr-2 ${
                          whatsapp.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {whatsapp.status === 'active' ? 'Activo' : 'Inactivo'}
                        </span>
                        <span className="text-xs text-gray-500">Último mensaje: {whatsapp.lastMessage}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Mensajes totales</div>
                    <div className="text-2xl font-bold">{whatsapp.messagesTotal}</div>
                    <div className="text-xs text-gray-500">Agente: {whatsapp.agent}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Variables de entorno</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key OpenAI
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  placeholder="sk-..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webhook URL
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  placeholder="https://..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  WhatsApp Token
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  placeholder="Token de WhatsApp Business API"
                />
              </div>
              <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
                Guardar configuración
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignDetail;