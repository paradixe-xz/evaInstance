import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Send, Phone, MoreVertical, User, Check, CheckCheck, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { MainLayout } from '../../components/layout/MainLayout';
import { useAuth } from '../../contexts/AuthContext';
import { chatService } from '../../services/api';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Switch } from '../../components/ui/switch';
import { cn } from '../../lib/utils';

// Types
interface ChatUser {
    id: number;
    phone_number: string;
    name: string;
    is_active: boolean;
    total_messages: number;
    last_activity: string | null;
    ai_paused?: boolean;
}

interface Message {
    id: number;
    content: string;
    direction: 'incoming' | 'outgoing';
    timestamp: string;
    is_read: boolean;
    is_delivered: boolean;
    message_type: string;
}

interface ChatHistoryResponse {
    phone_number: string;
    messages: Message[];
    total: number;
}

export function WhatsAppPage() {
    const { logout } = useAuth();
    const queryClient = useQueryClient();
    const [selectedUser, setSelectedUser] = useState<ChatUser | null>(null);
    const [messageInput, setMessageInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [searchTerm, setSearchTerm] = useState('');

    // Fetch users
    const { data: usersData, isLoading: isLoadingUsers } = useQuery({
        queryKey: ['chat-users'],
        queryFn: () => chatService.getUsers({ limit: 50 }),
        refetchInterval: 30000, // Refresh every 30s
    });

    // Fetch chat history for selected user
    const { data: chatHistory, isLoading: isLoadingHistory } = useQuery({
        queryKey: ['chat-history', selectedUser?.phone_number],
        queryFn: () => selectedUser ? chatService.getChatHistory(selectedUser.phone_number, { limit: 50 }) : null,
        enabled: !!selectedUser,
        refetchInterval: 5000, // Refresh every 5s when chat is open
    });

    // Send message mutation
    const sendMessageMutation = useMutation({
        mutationFn: ({ phoneNumber, message }: { phoneNumber: string; message: string }) =>
            chatService.sendMessage(phoneNumber, message),
        onSuccess: () => {
            setMessageInput('');
            queryClient.invalidateQueries({ queryKey: ['chat-history', selectedUser?.phone_number] });
            // Also refresh users to update last activity/message count
            queryClient.invalidateQueries({ queryKey: ['chat-users'] });
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Error al enviar mensaje');
        }
    });

    // Toggle AI Status Mutation
    const toggleAiMutation = useMutation({
        mutationFn: ({ userId, paused }: { userId: number; paused: boolean }) =>
            chatService.updateUserAiStatus(userId, paused),
        onSuccess: (data) => {
            // Update local state for immediate feedback
            if (selectedUser) {
                setSelectedUser(prev => prev ? { ...prev, ai_paused: data.ai_paused } : null);
            }
            // Invalidate users query to ensure data consistency
            queryClient.invalidateQueries({ queryKey: ['chat-users'] });
            toast.success(data.ai_paused ? 'IA pausada para este usuario' : 'IA activada para este usuario');
        },
        onError: () => {
            toast.error('Error al cambiar el estado de la IA');
        }
    });

    // Scroll to bottom on new messages
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [chatHistory]);

    const handleSendMessage = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedUser || !messageInput.trim()) return;

        sendMessageMutation.mutate({
            phoneNumber: selectedUser.phone_number,
            message: messageInput
        });
    };

    const filteredUsers = usersData?.users.filter((user: ChatUser) =>
        user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.phone_number.includes(searchTerm)
    ) || [];

    const formatTime = (dateString: string) => {
        return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return formatTime(dateString);
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Ayer';
        } else {
            return date.toLocaleDateString();
        }
    };

    return (
        <MainLayout onLogout={logout}>
            <div className="flex h-[calc(100vh-100px)] bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-200">

                {/* Sidebar - Users List */}
                <div className="w-80 border-r border-gray-200 flex flex-col bg-gray-50/50">
                    <div className="p-4 border-b border-gray-200 bg-white">
                        <h2 className="text-lg font-semibold mb-4">Mensajes</h2>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                placeholder="Buscar conversación..."
                                className="pl-9 bg-gray-50 border-gray-200"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {isLoadingUsers ? (
                            <div className="flex justify-center p-8">
                                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                            </div>
                        ) : filteredUsers.length === 0 ? (
                            <div className="p-8 text-center text-gray-500 text-sm">
                                No se encontraron conversaciones
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-100">
                                {filteredUsers.map((user: ChatUser) => (
                                    <button
                                        key={user.id}
                                        onClick={() => setSelectedUser(user)}
                                        className={cn(
                                            "w-full p-4 flex items-start gap-3 hover:bg-gray-50 transition-colors text-left",
                                            selectedUser?.id === user.id && "bg-blue-50/50 hover:bg-blue-50"
                                        )}
                                    >
                                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center flex-shrink-0">
                                            <User className="h-5 w-5 text-blue-600" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-baseline mb-1">
                                                <span className="font-medium text-gray-900 truncate">{user.name || user.phone_number}</span>
                                                {user.last_activity && (
                                                    <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                                                        {formatDate(user.last_activity)}
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-500 truncate">
                                                {user.phone_number}
                                            </p>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 flex flex-col bg-[#efeae2] relative">
                    {/* Chat Background Pattern */}
                    <div className="absolute inset-0 opacity-[0.06] bg-[url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png')] pointer-events-none" />

                    {selectedUser ? (
                        <>
                            {/* Chat Header */}
                            <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 relative z-10">
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center">
                                        <User className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900">{selectedUser.name || selectedUser.phone_number}</h3>
                                        <p className="text-xs text-gray-500">{selectedUser.phone_number}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" size="icon" className="text-gray-500">
                                        <Phone className="h-5 w-5" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="text-gray-500">
                                        <MoreVertical className="h-5 w-5" />
                                    </Button>
                                </div>
                            </div>

                            {/* AI Toggle Header */}
                            <div className="bg-gray-50 px-6 py-2 border-b border-gray-200 flex justify-end items-center gap-2">
                                <span className={cn(
                                    "text-xs font-medium transition-colors",
                                    selectedUser.ai_paused ? "text-gray-500" : "text-green-600"
                                )}>
                                    {selectedUser.ai_paused ? "IA Pausada" : "IA Activa"}
                                </span>
                                <Switch
                                    checked={!selectedUser.ai_paused}
                                    onCheckedChange={(checked) => {
                                        if (selectedUser) {
                                            toggleAiMutation.mutate({
                                                userId: selectedUser.id,
                                                paused: !checked
                                            });
                                        }
                                    }}
                                    className={cn(
                                        "data-[state=checked]:bg-green-500"
                                    )}
                                />
                            </div>

                            {/* Messages Area */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-4 relative z-10">
                                {isLoadingHistory ? (
                                    <div className="flex justify-center p-8">
                                        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                                    </div>
                                ) : chatHistory?.messages.length === 0 ? (
                                    <div className="text-center py-12">
                                        <div className="bg-white/80 backdrop-blur-sm inline-block px-4 py-2 rounded-lg shadow-sm text-sm text-gray-500">
                                            No hay mensajes en esta conversación
                                        </div>
                                    </div>
                                ) : (
                                    chatHistory?.messages.map((msg: Message) => (
                                        <div
                                            key={msg.id}
                                            className={cn(
                                                "flex w-full",
                                                msg.direction === 'outgoing' ? "justify-end" : "justify-start"
                                            )}
                                        >
                                            <div
                                                className={cn(
                                                    "max-w-[70%] rounded-lg px-4 py-2 shadow-sm relative group",
                                                    msg.direction === 'outgoing'
                                                        ? "bg-[#d9fdd3] text-gray-900 rounded-tr-none"
                                                        : "bg-white text-gray-900 rounded-tl-none"
                                                )}
                                            >
                                                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                                                    {msg.content}
                                                </p>
                                                <div className="flex items-center justify-end gap-1 mt-1">
                                                    <span className="text-[10px] text-gray-500">
                                                        {formatTime(msg.timestamp)}
                                                    </span>
                                                    {msg.direction === 'outgoing' && (
                                                        <span className="text-blue-500">
                                                            {msg.is_read ? (
                                                                <CheckCheck className="h-3 w-3" />
                                                            ) : (
                                                                <Check className="h-3 w-3" />
                                                            )}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                                <div ref={messagesEndRef} />
                            </div>

                            {/* Input Area */}
                            <div className="bg-white p-4 border-t border-gray-200 relative z-10">
                                <form onSubmit={handleSendMessage} className="flex gap-2">
                                    <Input
                                        value={messageInput}
                                        onChange={(e) => setMessageInput(e.target.value)}
                                        placeholder="Escribe un mensaje..."
                                        className="flex-1 bg-gray-50 border-gray-200 focus:bg-white transition-colors"
                                    />
                                    <Button
                                        type="submit"
                                        disabled={!messageInput.trim() || sendMessageMutation.isPending}
                                        className="bg-[#00a884] hover:bg-[#008f6f] text-white"
                                    >
                                        {sendMessageMutation.isPending ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Send className="h-4 w-4" />
                                        )}
                                    </Button>
                                </form>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500 relative z-10">
                            <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
                                <User className="h-8 w-8 text-gray-400" />
                            </div>
                            <h3 className="text-lg font-medium text-gray-700">WhatsApp Web</h3>
                            <p className="text-sm mt-2">Selecciona una conversación para comenzar</p>
                        </div>
                    )}
                </div>
            </div>
        </MainLayout>
    );
}
