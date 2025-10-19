import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Send, Paperclip, Mic, LogOut, Bell, Settings, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import api, { createWebSocket } from '../lib/api';
import { clearAuth, getAuth } from '../lib/auth';
import { formatWhatsApp, isWithinBusinessHours, shouldShowQueuePopup, markQueuePopupShown } from '../utils/formatters';
import AlertModal from '../components/AlertModal';

const ClientChat = () => {
  const navigate = useNavigate();
  const auth = getAuth();
  const [userData, setUserData] = useState(auth.userData);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [credentials, setCredentials] = useState({ pinned_user: '', pinned_pass: '' });
  const [notices, setNotices] = useState([]);
  const [showNotices, setShowNotices] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [newPin, setNewPin] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [hasNewNotices, setHasNewNotices] = useState(false);
  const [onlineStatus, setOnlineStatus] = useState('Carregando...');
  const [lastNoticeCount, setLastNoticeCount] = useState(0);
  const [alertModal, setAlertModal] = useState({ isOpen: false, title: '', message: '', icon: 'info' });
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const queueTimerRef = useRef(null);

  useEffect(() => {
    loadMessages();
    loadNotices();
    loadUserData();
    checkOnlineStatus();
    
    // Check notices every 30 seconds
    const noticesInterval = setInterval(() => {
      checkForNewNotices();
    }, 30000);
    
    // Check online status every minute
    const statusInterval = setInterval(() => {
      checkOnlineStatus();
    }, 60000);
    
    return () => {
      clearInterval(noticesInterval);
      clearInterval(statusInterval);
      if (queueTimerRef.current) {
        clearTimeout(queueTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!userData?.id) return;
    const ws = createWebSocket(userData.id);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.message]);
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE');
        audio.play().catch(() => {});
      }
      if (data.type === 'credentials_updated') {
        setCredentials({ pinned_user: data.pinned_user, pinned_pass: data.pinned_pass });
      }
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [userData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = async () => {
    try {
      const ticketsRes = await api.get('/tickets', { params: { status: null } });
      const myTicket = ticketsRes.data.find(t => t.client_id === userData.id);
      if (myTicket) {
        const { data } = await api.get(`/messages/${myTicket.id}`);
        setMessages(data);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const loadNotices = async () => {
    try {
      const { data } = await api.get('/notices');
      setNotices(data);
      
      // Check if there are new notices
      const stored = parseInt(localStorage.getItem('last_notice_count') || '0');
      if (data.length > stored) {
        setHasNewNotices(true);
      }
      setLastNoticeCount(data.length);
    } catch (error) {
      console.error('Error loading notices:', error);
    }
  };
  
  const checkForNewNotices = async () => {
    try {
      const { data } = await api.get('/notices');
      const stored = parseInt(localStorage.getItem('last_notice_count') || '0');
      if (data.length > stored) {
        setHasNewNotices(true);
      }
    } catch (error) {
      console.error('Error checking notices:', error);
    }
  };
  
  const checkOnlineStatus = async () => {
    try {
      const { data } = await api.get('/agents/online-status');
      if (data.online > 0) {
        setOnlineStatus('Online');
      } else if (isWithinBusinessHours()) {
        setOnlineStatus('Ausente');
      } else {
        setOnlineStatus('Fora de horário');
      }
    } catch (error) {
      // Fallback: check business hours
      setOnlineStatus(isWithinBusinessHours() ? 'Ausente' : 'Fora de horário');
    }
  };

  const loadUserData = async () => {
    try {
      const { data } = await api.get('/users/me');
      setUserData(data);  // Update userData with fresh data from server
      setCredentials({ pinned_user: data.pinned_user, pinned_pass: data.pinned_pass });
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!messageText.trim()) return;
    
    if (!userData?.id) {
      toast.error('Erro: Dados do usuário não carregados');
      return;
    }
    
    // Check business hours
    if (!isWithinBusinessHours()) {
      setAlertModal({
        isOpen: true,
        title: 'Fora do Horário',
        message: 'Estamos fora do horário de atendimento (9h às 23h). Sua mensagem será respondida assim que possível.',
        icon: 'clock'
      });
    }
    
    // Check if agents are online
    else if (onlineStatus === 'Ausente' && isWithinBusinessHours()) {
      setAlertModal({
        isOpen: true,
        title: 'Ausente',
        message: 'Estamos ausentes no momento. Em breve retornaremos e responderemos sua mensagem.',
        icon: 'warning'
      });
    }
    
    try {
      // Get first available agent
      const agents = await api.get('/agents');
      if (!agents.data || agents.data.length === 0) {
        toast.error('Nenhum atendente disponível no momento');
        return;
      }
      const agentId = agents.data[0].id;
      
      console.log('Sending message:', { from_id: userData.id, to_id: agentId });
      
      // Send message (backend will create ticket automatically if needed)
      await api.post('/messages', {
        ticket_id: '',  // Backend creates ticket for new clients
        from_type: 'client',
        from_id: userData.id,
        to_type: 'agent',
        to_id: agentId,
        kind: 'text',
        text: messageText,
        file_url: ''
      });
      
      setMessageText('');
      toast.success('Mensagem enviada!');
      setTimeout(loadMessages, 500);
      
      // Show queue popup after 10 seconds (once per day)
      if (shouldShowQueuePopup()) {
        queueTimerRef.current = setTimeout(async () => {
          try {
            const { data } = await api.get('/tickets/counts');
            const queueCount = data.EM_ESPERA || 0;
            setAlertModal({
              isOpen: true,
              title: 'Fila de Espera',
              message: `Você está na fila de espera. ${queueCount} pessoa(s) aguardando atendimento. Em breve você será atendido!`,
              icon: 'queue'
            });
            markQueuePopupShown();
          } catch (error) {
            console.error('Error getting queue count:', error);
          }
        }, 10000);
      }
    } catch (error) {
      console.error('Send error:', error);
      toast.error(error.response?.data?.detail || 'Erro ao enviar mensagem');
    }
  };

  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const agents = await api.get('/agents');
      if (!agents.data || agents.data.length === 0) {
        toast.error('Nenhum atendente disponível');
        return;
      }
      const agentId = agents.data[0].id;
      
      await api.post('/messages', {
        ticket_id: '',  // Backend creates ticket automatically
        from_type: 'client',
        from_id: userData.id,
        to_type: 'agent',
        to_id: agentId,
        kind: data.kind,
        text: '',
        file_url: data.url
      });
      
      toast.success('Arquivo enviado!');
      setTimeout(loadMessages, 500);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Erro ao enviar arquivo');
    }
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks = [];
      
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const file = new File([blob], 'audio.webm', { type: 'audio/webm' });
        await handleFileUpload(file);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      
      setTimeout(() => {
        if (mediaRecorder.state !== 'inactive') {
          mediaRecorder.stop();
          setIsRecording(false);
        }
      }, 60000);
    } catch (error) {
      toast.error('Erro ao acessar microfone');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleUpdatePin = async () => {
    try {
      await api.put('/users/me/pin', { pin: newPin });
      toast.success('PIN atualizado!');
      setNewPin('');
      setShowSettings(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar PIN');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50 flex items-center justify-center p-4">
      <div className="phone-mockup w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <MessageCircle className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-semibold">Suporte</h1>
              <p className="text-xs opacity-90">{onlineStatus}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              data-testid="notices-btn"
              variant="ghost"
              size="icon"
              onClick={() => {
                setShowNotices(true);
                setHasNewNotices(false);
                localStorage.setItem('last_notice_count', lastNoticeCount.toString());
              }}
              className={`text-white hover:bg-white/20 relative ${hasNewNotices ? 'pulse' : ''}`}
            >
              <Bell className={`w-5 h-5 ${hasNewNotices ? 'text-red-300' : ''}`} />
              {hasNewNotices && (
                <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
              )}
            </Button>
            <Button
              data-testid="settings-btn"
              variant="ghost"
              size="icon"
              onClick={() => setShowSettings(true)}
              className="text-white hover:bg-white/20"
            >
              <Settings className="w-5 h-5" />
            </Button>
            <Button
              data-testid="client-logout-btn"
              variant="ghost"
              size="icon"
              onClick={() => { clearAuth(); navigate('/'); }}
              className="text-white hover:bg-white/20"
            >
              <LogOut className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Credentials Bar */}
        {(credentials.pinned_user || credentials.pinned_pass) && (
          <div className="bg-cyan-100 border-b border-cyan-200 px-4 py-2 text-sm">
            <span className="font-medium">Usuário:</span> {credentials.pinned_user} • 
            <span className="font-medium">Senha:</span> {credentials.pinned_pass}
          </div>
        )}

        {/* Messages */}
        <div className="h-[500px] bg-slate-50 p-4 overflow-y-auto">
          <div className="space-y-3">
            {messages.map(msg => (
              <div key={msg.id} className={`flex ${msg.from_type === 'client' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] p-3 rounded-2xl shadow-sm ${
                    msg.from_type === 'client'
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : 'bg-white text-slate-900 rounded-bl-sm'
                  }`}
                >
                  {msg.kind === 'text' && <p className="whitespace-pre-wrap break-words text-sm">{msg.text}</p>}
                  {msg.kind === 'image' && <img src={msg.file_url} alt="" className="max-w-full rounded-lg" />}
                  {msg.kind === 'video' && <video src={msg.file_url} controls className="max-w-full rounded-lg" />}
                  {msg.kind === 'audio' && <audio src={msg.file_url} controls className="w-full" />}
                  {msg.kind === 'pix' && (
                    <div>
                      <p className="font-semibold text-sm mb-2">Chave PIX</p>
                      <code className="text-xs bg-black/10 px-2 py-1 rounded block mb-2">{msg.text}</code>
                      <Button
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(msg.text);
                          toast.success('PIX copiado!');
                        }}
                        className="w-full"
                      >
                        Copiar PIX
                      </Button>
                    </div>
                  )}
                  <p className="text-[10px] mt-1 opacity-70">
                    {new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="bg-white border-t border-slate-200 p-3">
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept="image/*,video/*"
              onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
            />
            <Button
              data-testid="attach-btn"
              variant="outline"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
            >
              <Paperclip className="w-4 h-4" />
            </Button>
            <Button
              data-testid="record-btn"
              variant="outline"
              size="icon"
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              className={isRecording ? 'bg-red-100 border-red-300' : ''}
            >
              <Mic className={`w-4 h-4 ${isRecording ? 'text-red-600' : ''}`} />
            </Button>
            <Input
              data-testid="client-message-input"
              placeholder="Digite sua mensagem..."
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              className="flex-1"
            />
            <Button data-testid="send-message-btn" onClick={handleSendMessage} className="bg-blue-600 hover:bg-blue-700">
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Notices Dialog */}
      <Dialog open={showNotices} onOpenChange={setShowNotices}>
        <DialogContent data-testid="notices-dialog" className="max-w-md">
          <DialogHeader>
            <DialogTitle>Avisos</DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[400px]">
            <div className="space-y-4">
              {notices.map(notice => (
                <Card key={notice.id} className="p-4">
                  {notice.kind === 'text' && <p>{notice.text}</p>}
                  {notice.kind === 'image' && <img src={notice.file_url} alt="" className="w-full rounded-lg" />}
                  {notice.kind === 'video' && <video src={notice.file_url} controls className="w-full rounded-lg" />}
                  {notice.kind === 'audio' && <audio src={notice.file_url} controls className="w-full" />}
                  <p className="text-xs text-slate-500 mt-2">
                    {new Date(notice.created_at).toLocaleString('pt-BR')}
                  </p>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent data-testid="settings-dialog" className="max-w-md">
          <DialogHeader>
            <DialogTitle>Configurações</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-2">Alterar PIN (2 dígitos)</label>
              <div className="flex gap-2">
                <Input
                  data-testid="new-pin-input"
                  type="password"
                  placeholder="Novo PIN"
                  value={newPin}
                  onChange={(e) => setNewPin(e.target.value.replace(/\D/g, '').slice(0, 2))}
                  maxLength={2}
                />
                <Button data-testid="update-pin-btn" onClick={handleUpdatePin}>
                  Atualizar
                </Button>
              </div>
            </div>
            <div className="pt-4 border-t">
              <p className="text-sm text-slate-600">
                <span className="font-medium">WhatsApp:</span> {userData.whatsapp}
              </p>
              {userData.display_name && (
                <p className="text-sm text-slate-600 mt-1">
                  <span className="font-medium">Nome:</span> {userData.display_name}
                </p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Alert Modal */}
      <AlertModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal({ ...alertModal, isOpen: false })}
        title={alertModal.title}
        message={alertModal.message}
        icon={alertModal.icon}
        autoCloseDelay={30000}
      />
    </div>
  );
};

export default ClientChat;
