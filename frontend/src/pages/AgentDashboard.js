import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Headphones, LogOut, Send, Paperclip, Mic, Phone, User, Key, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import api, { createWebSocket } from '../lib/api';
import { clearAuth, getAuth } from '../lib/auth';

const AgentDashboard = () => {
  const navigate = useNavigate();
  const { userData } = getAuth();
  const [status, setStatus] = useState('EM_ESPERA');
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [counts, setCounts] = useState({ EM_ESPERA: 0, ATENDENDO: 0, FINALIZADAS: 0 });
  const [config, setConfig] = useState({ quick_blocks: [] });
  const [pinnedUser, setPinnedUser] = useState('');
  const [pinnedPass, setPinnedPass] = useState('');
  const [resetPhone, setResetPhone] = useState('');
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadTickets();
    loadCounts();
    loadConfig();
    const interval = setInterval(loadCounts, 5000);
    return () => clearInterval(interval);
  }, [status]);

  useEffect(() => {
    if (!userData?.id) return;
    const ws = createWebSocket(userData.id);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        if (selectedTicket && data.message.ticket_id === selectedTicket.id) {
          setMessages(prev => [...prev, data.message]);
        }
        loadTickets();
      }
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [userData, selectedTicket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadTickets = async () => {
    try {
      const { data } = await api.get('/tickets', { params: { status } });
      setTickets(data);
    } catch (error) {
      console.error('Error loading tickets:', error);
    }
  };

  const loadCounts = async () => {
    try {
      const { data } = await api.get('/tickets/counts');
      setCounts(data);
    } catch (error) {
      console.error('Error loading counts:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const { data } = await api.get('/config');
      setConfig(data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const loadMessages = async (ticketId) => {
    try {
      const { data } = await api.get(`/messages/${ticketId}`);
      setMessages(data);
    } catch (error) {
      toast.error('Erro ao carregar mensagens');
    }
  };

  const handleSelectTicket = (ticket) => {
    setSelectedTicket(ticket);
    loadMessages(ticket.id);
  };

  const handleSendMessage = async (newStatus = null) => {
    if (!selectedTicket || !messageText.trim()) return;
    
    try {
      await api.post('/messages', {
        ticket_id: selectedTicket.id,
        from_type: 'agent',
        from_id: userData.id,
        to_type: 'client',
        to_id: selectedTicket.client_id,
        kind: 'text',
        text: messageText,
        file_url: ''
      });
      
      if (newStatus) {
        await api.post(`/tickets/${selectedTicket.id}/status`, { status: newStatus });
        loadTickets();
      }
      
      setMessageText('');
      loadMessages(selectedTicket.id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao enviar mensagem');
    }
  };

  const handleFileUpload = async (file) => {
    if (!selectedTicket) return;
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      await api.post('/messages', {
        ticket_id: selectedTicket.id,
        from_type: 'agent',
        from_id: userData.id,
        to_type: 'client',
        to_id: selectedTicket.client_id,
        kind: data.kind,
        text: '',
        file_url: data.url
      });
      
      loadMessages(selectedTicket.id);
      toast.success('Arquivo enviado!');
    } catch (error) {
      toast.error('Erro ao enviar arquivo');
    }
  };

  const handlePinCredentials = async () => {
    if (!selectedTicket) return;
    try {
      await api.put(`/users/${selectedTicket.client_id}/pin-credentials`, {
        pinned_user: pinnedUser,
        pinned_pass: pinnedPass
      });
      toast.success('Credenciais fixadas!');
      setPinnedUser('');
      setPinnedPass('');
    } catch (error) {
      toast.error('Erro ao fixar credenciais');
    }
  };

  const handleResetPin = async () => {
    try {
      await api.post('/users/reset-pin', { whatsapp: resetPhone });
      toast.success('PIN resetado!');
      setResetPhone('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao resetar PIN');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-full mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Headphones className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Painel do Atendente</h1>
              <p className="text-sm text-slate-600">{userData?.name}</p>
            </div>
          </div>
          <Button data-testid="agent-logout-btn" onClick={() => { clearAuth(); navigate('/'); }} variant="outline" size="sm">
            <LogOut className="w-4 h-4 mr-2" />
            Sair
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
          {/* Tools */}
          <div className="p-4 border-b border-slate-200 space-y-3">
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-700">Fixar Credenciais</label>
              <div className="flex gap-2">
                <Input data-testid="pin-user-input" placeholder="Usuário" value={pinnedUser} onChange={(e) => setPinnedUser(e.target.value)} size="sm" />
                <Input data-testid="pin-pass-input" placeholder="Senha" value={pinnedPass} onChange={(e) => setPinnedPass(e.target.value)} size="sm" />
              </div>
              <Button data-testid="pin-credentials-btn" onClick={handlePinCredentials} size="sm" className="w-full">
                Fixar
              </Button>
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-700">Resetar PIN</label>
              <div className="flex gap-2">
                <Input data-testid="reset-phone-input" placeholder="WhatsApp" value={resetPhone} onChange={(e) => setResetPhone(e.target.value)} size="sm" />
                <Button data-testid="reset-pin-btn" onClick={handleResetPin} size="sm">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <Tabs value={status} onValueChange={setStatus} className="flex-1 flex flex-col">
            <TabsList className="grid grid-cols-3 m-2">
              <TabsTrigger value="EM_ESPERA" data-testid="tab-em-espera" className="text-xs">
                Espera <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full text-[10px]">{counts.EM_ESPERA}</span>
              </TabsTrigger>
              <TabsTrigger value="ATENDENDO" data-testid="tab-atendendo" className="text-xs">
                Atendendo <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded-full text-[10px]">{counts.ATENDENDO}</span>
              </TabsTrigger>
              <TabsTrigger value="FINALIZADAS" data-testid="tab-finalizadas" className="text-xs">
                Finalizadas <span className="ml-1 px-1.5 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px]">{counts.FINALIZADAS}</span>
              </TabsTrigger>
            </TabsList>

            <ScrollArea className="flex-1">
              <div className="p-2 space-y-2">
                {tickets.map(ticket => (
                  <Card
                    key={ticket.id}
                    data-testid={`ticket-${ticket.id}`}
                    className={`p-3 cursor-pointer transition-all hover:shadow-md ${
                      selectedTicket?.id === ticket.id ? 'border-2 border-indigo-500 bg-indigo-50' : ''
                    }`}
                    onClick={() => handleSelectTicket(ticket)}
                  >
                    <div className="flex items-center gap-3">
                      {ticket.client_avatar && (
                        <img src={ticket.client_avatar} alt="" className="w-10 h-10 rounded-full object-cover" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-slate-900 truncate">
                          {ticket.client_name || ticket.client_whatsapp}
                        </p>
                        <p className="text-xs text-slate-500 truncate">{ticket.client_whatsapp}</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </Tabs>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-slate-100">
          {selectedTicket ? (
            <>
              {/* Chat Header */}
              <div className="bg-white border-b border-slate-200 p-4 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">
                    {selectedTicket.client_name || selectedTicket.client_whatsapp}
                  </h3>
                  <p className="text-sm text-slate-600">
                    Usuário: <span className="font-mono">{selectedTicket.client_whatsapp}</span>
                  </p>
                </div>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {messages.map(msg => (
                    <div key={msg.id} className={`flex ${msg.from_type === 'agent' ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`max-w-[70%] p-3 rounded-2xl ${
                          msg.from_type === 'agent'
                            ? 'bg-indigo-600 text-white rounded-br-sm'
                            : 'bg-white text-slate-900 rounded-bl-sm shadow-sm'
                        }`}
                      >
                        {msg.kind === 'text' && <p className="whitespace-pre-wrap break-words">{msg.text}</p>}
                        {msg.kind === 'image' && <img src={msg.file_url} alt="" className="max-w-full rounded-lg" />}
                        {msg.kind === 'video' && <video src={msg.file_url} controls className="max-w-full rounded-lg" />}
                        {msg.kind === 'audio' && <audio src={msg.file_url} controls className="w-full" />}
                        {msg.kind === 'pix' && (
                          <div>
                            <p className="font-semibold mb-2">Chave PIX</p>
                            <code className="text-xs bg-black/10 px-2 py-1 rounded">{msg.text}</code>
                          </div>
                        )}
                        <p className="text-xs mt-1 opacity-70">
                          {new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Quick Messages */}
              {config.quick_blocks.length > 0 && (
                <div className="bg-white border-t border-slate-200 p-2 flex flex-wrap gap-2">
                  {config.quick_blocks.map((block, idx) => (
                    <Button
                      key={idx}
                      data-testid={`quick-block-${idx}`}
                      size="sm"
                      variant="outline"
                      onClick={() => setMessageText(block.text)}
                      className="text-xs"
                    >
                      {block.name}
                    </Button>
                  ))}
                </div>
              )}

              {/* Input */}
              <div className="bg-white border-t border-slate-200 p-4">
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
                  />
                  <Button
                    data-testid="attach-file-btn"
                    variant="outline"
                    size="icon"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="w-4 h-4" />
                  </Button>
                  <Textarea
                    data-testid="message-input"
                    placeholder="Digite sua mensagem..."
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage('ATENDENDO');
                      }
                    }}
                    className="flex-1 resize-none"
                    rows={2}
                  />
                  <div className="flex flex-col gap-2">
                    <Button data-testid="send-and-continue-btn" onClick={() => handleSendMessage('ATENDENDO')} size="sm" className="bg-indigo-600 hover:bg-indigo-700">
                      <Send className="w-4 h-4" />
                    </Button>
                    <Button data-testid="send-and-wait-btn" onClick={() => handleSendMessage('EM_ESPERA')} size="sm" variant="outline">
                      Espera
                    </Button>
                    <Button data-testid="send-and-finish-btn" onClick={() => handleSendMessage('FINALIZADAS')} size="sm" variant="outline">
                      Finalizar
                    </Button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-slate-500">
                <Headphones className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Selecione um ticket para iniciar o atendimento</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;
