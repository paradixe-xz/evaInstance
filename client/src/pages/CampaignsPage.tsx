import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Play, Pause, BarChart3, Trash2 } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Campaign {
    id: number;
    name: string;
    slug: string;
    type: string;
    status: string;
    description?: string;
    total_calls?: number;
    total_whatsapp_messages?: number;
    success_rate?: number;
}

export default function CampaignsPage() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newCampaign, setNewCampaign] = useState({
        name: '',
        slug: '',
        type: 'whatsapp',
        description: ''
    });

    useEffect(() => {
        fetchCampaigns();
    }, []);

    const fetchCampaigns = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/v1/campaigns/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            setCampaigns(data);
        } catch (error) {
            console.error('Error fetching campaigns:', error);
        } finally {
            setLoading(false);
        }
    };

    const createCampaign = async () => {
        try {
            const response = await fetch('/api/v1/campaigns/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    ...newCampaign,
                    status: 'draft'
                })
            });

            if (response.ok) {
                setIsCreateOpen(false);
                setNewCampaign({ name: '', slug: '', type: 'whatsapp', description: '' });
                fetchCampaigns();
            }
        } catch (error) {
            console.error('Error creating campaign:', error);
        }
    };

    const toggleCampaign = async (id: number, currentStatus: string) => {
        const endpoint = currentStatus === 'active' ? 'stop' : 'start';
        try {
            await fetch(`/api/v1/campaigns/${id}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            fetchCampaigns();
        } catch (error) {
            console.error('Error toggling campaign:', error);
        }
    };

    const deleteCampaign = async (id: number) => {
        if (!confirm('¿Estás seguro de eliminar esta campaña?')) return;

        try {
            await fetch(`/api/v1/campaigns/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            fetchCampaigns();
        } catch (error) {
            console.error('Error deleting campaign:', error);
        }
    };

    const getStatusBadge = (status: string) => {
        const variants: Record<string, string> = {
            active: 'bg-green-500',
            paused: 'bg-yellow-500',
            draft: 'bg-gray-500',
            completed: 'bg-blue-500'
        };
        return <Badge className={variants[status] || 'bg-gray-500'}>{status}</Badge>;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-lg">Cargando campañas...</div>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Campañas</h1>
                    <p className="text-muted-foreground">Gestiona tus campañas de marketing</p>
                </div>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            Nueva Campaña
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Crear Nueva Campaña</DialogTitle>
                            <DialogDescription>
                                Configura una nueva campaña de marketing
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div>
                                <Label htmlFor="name">Nombre</Label>
                                <Input
                                    id="name"
                                    value={newCampaign.name}
                                    onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                                    placeholder="Mi Campaña"
                                />
                            </div>
                            <div>
                                <Label htmlFor="slug">Slug</Label>
                                <Input
                                    id="slug"
                                    value={newCampaign.slug}
                                    onChange={(e) => setNewCampaign({ ...newCampaign, slug: e.target.value })}
                                    placeholder="mi-campana"
                                />
                            </div>
                            <div>
                                <Label htmlFor="type">Tipo</Label>
                                <Select value={newCampaign.type} onValueChange={(value) => setNewCampaign({ ...newCampaign, type: value })}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="whatsapp">WhatsApp</SelectItem>
                                        <SelectItem value="calls">Llamadas</SelectItem>
                                        <SelectItem value="email">Email</SelectItem>
                                        <SelectItem value="mixed">Mixta</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <Label htmlFor="description">Descripción</Label>
                                <Textarea
                                    id="description"
                                    value={newCampaign.description}
                                    onChange={(e) => setNewCampaign({ ...newCampaign, description: e.target.value })}
                                    placeholder="Descripción de la campaña..."
                                />
                            </div>
                            <Button onClick={createCampaign} className="w-full">
                                Crear Campaña
                            </Button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {campaigns.map((campaign) => (
                    <Card key={campaign.id}>
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <div>
                                    <CardTitle>{campaign.name}</CardTitle>
                                    <CardDescription>{campaign.type}</CardDescription>
                                </div>
                                {getStatusBadge(campaign.status)}
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {campaign.description && (
                                <p className="text-sm text-muted-foreground">{campaign.description}</p>
                            )}

                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <p className="text-muted-foreground">Llamadas</p>
                                    <p className="font-semibold">{campaign.total_calls || 0}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Mensajes</p>
                                    <p className="font-semibold">{campaign.total_whatsapp_messages || 0}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground">Tasa de Éxito</p>
                                    <p className="font-semibold">{campaign.success_rate || 0}%</p>
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => toggleCampaign(campaign.id, campaign.status)}
                                    className="flex-1"
                                >
                                    {campaign.status === 'active' ? (
                                        <>
                                            <Pause className="mr-2 h-4 w-4" />
                                            Pausar
                                        </>
                                    ) : (
                                        <>
                                            <Play className="mr-2 h-4 w-4" />
                                            Iniciar
                                        </>
                                    )}
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => window.location.href = `/campaigns/${campaign.id}/analytics`}
                                >
                                    <BarChart3 className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => deleteCampaign(campaign.id)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {campaigns.length === 0 && (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <p className="text-muted-foreground mb-4">No tienes campañas creadas</p>
                        <Button onClick={() => setIsCreateOpen(true)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Crear Primera Campaña
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
