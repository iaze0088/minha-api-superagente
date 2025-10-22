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
import InstallPWA from '../components/InstallPWA';

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
  const [showNamePopup, setShowNamePopup] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [firstMessageSent, setFirstMessageSent] = useState(false);
  const [pixKey, setPixKey] = useState('');
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const queueTimerRef = useRef(null);
  const notificationAudioRef = useRef(null);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);
  const [config, setConfig] = useState({ support_avatar: '' });
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const avatarInputRef = useRef(null);

  // Função para conectar WebSocket com reconexão automática
  const connectWebSocket = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Já conectado
    }
    
    if (!userData?.id) {
      console.warn('⚠️ Aguardando dados do usuário para conectar WebSocket');
      return;
    }
    
    const ws = createWebSocket(userData.id);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket conectado - Mensagens em tempo real ativas');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Nova mensagem via WebSocket:', data);
      
      // Mensagens de chat (novo tipo ou tipo message)
      if ((data.type === 'new_message' || data.type === 'message') && data.message) {
        setMessages(prev => {
          // Evitar duplicação
          if (prev.some(m => m.id === data.message.id)) {
            console.log('⚠️ Mensagem duplicada ignorada');
            return prev;
          }
          console.log('✅ Nova mensagem adicionada:', data.message.text?.substring(0, 50));
          
          // Som de notificação para mensagens do agente ou IA
          if (data.message.from_type === 'agent' || data.message.from_type === 'ai') {
            // Tocar som de notificação do WhatsApp
            try {
              if (notificationAudioRef.current) {
                // Resetar o áudio para o início para permitir tocar novamente
                notificationAudioRef.current.currentTime = 0;
                notificationAudioRef.current.volume = 1.0;
                
                // Tentar tocar - usando Promise
                const playPromise = notificationAudioRef.current.play();
                
                if (playPromise !== undefined) {
                  playPromise
                    .then(() => {
                      console.log('🔊 Som de notificação tocado com sucesso!');
                    })
                    .catch((error) => {
                      console.warn('⚠️ Não foi possível tocar o som (autoplay bloqueado):', error);
                      // Tentar criar um novo áudio como fallback
                      try {
                        const fallbackAudio = new Audio('/notification.mp3');
                        fallbackAudio.volume = 1.0;
                        fallbackAudio.play().catch(e => console.log('Fallback também falhou:', e));
                      } catch (e) {
                        console.error('Erro no fallback:', e);
                      }
                    });
                }
              }
            } catch (e) {
              console.error('❌ Erro ao tocar som:', e);
            }
            
            // Vibrar dispositivo (se suportado)
            if ('vibrate' in navigator) {
              navigator.vibrate([200, 100, 200]);
            }
            
            // Mostrar notificação do navegador se página não estiver em foco
            if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
              try {
                const notification = new Notification('Nova mensagem de Suporte', {
                  body: data.message.text || 'Você recebeu uma nova mensagem',
                  icon: '/icon-192.png',
                  badge: '/icon-192.png',
                  tag: 'chat-message',
                  requireInteraction: false,
                  silent: false // Não silenciar - queremos o som do sistema também
                });
                
                // Clicar na notificação foca na janela
                notification.onclick = () => {
                  window.focus();
                  notification.close();
                };
                
                // Fechar notificação automaticamente após 5 segundos
                setTimeout(() => notification.close(), 5000);
              } catch (e) {
                console.error('Erro ao mostrar notificação:', e);
              }
            }
          }
          
          return [...prev, data.message];
        });
        
        // Scroll automático para a nova mensagem
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
      
      // Credenciais atualizadas
      if (data.type === 'credentials_updated') {
        setCredentials({ 
          pinned_user: data.pinned_user, 
          pinned_pass: data.pinned_pass 
        });
      }
      
      // Comentado: Não forçar logout automático
      // if (data.type === 'force_logout') {
      //   clearAuth();
      //   alert('Você foi desconectado porque outra pessoa fez login com suas credenciais.');
      //   navigate('/');
      // }
    };

    ws.onerror = (error) => {
      console.error('❌ Erro no WebSocket:', error);
    };

    ws.onclose = () => {
      console.log('⚠️ WebSocket desconectado, reconectando em 3s...');
      // Reconectar automaticamente após 3 segundos
      setTimeout(() => {
        if (auth.token) {
          connectWebSocket();
        }
      }, 3000);
    };
  };

  useEffect(() => {
    // Pre-carregar o áudio de notificação
    try {
      const audio = new Audio('/notification.mp3');
      audio.preload = 'auto';
      audio.volume = 1.0;
      notificationAudioRef.current = audio;
      console.log('✅ Áudio de notificação pré-carregado');
    } catch (e) {
      console.error('❌ Erro ao pré-carregar áudio:', e);
    }
    
    loadMessages();
    loadNotices();
    loadUserData();
    loadPixKey();
    checkOnlineStatus();
    
    // Solicitar permissão para notificações
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
    
    // Conectar WebSocket
    connectWebSocket();
    
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
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (queueTimerRef.current) {
        clearTimeout(queueTimerRef.current);
      }
      if (notificationAudioRef.current) {
        notificationAudioRef.current.pause();
        notificationAudioRef.current = null;
      }
    };
  }, []);

  // Reconectar WebSocket quando userData estiver disponível
  useEffect(() => {
    if (userData?.id && (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)) {
      console.log('🔄 Conectando WebSocket com userId:', userData.id);
      connectWebSocket();
    }
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

  const loadPixKey = async () => {
    try {
      const { data } = await api.get('/config');
      setPixKey(data.pix_key || '');
    } catch (error) {
      console.error('Error loading PIX key:', error);
    }
  };

  const checkNamePopup = async () => {
    try {
      const { data } = await api.get('/users/name-popup-status');
      if (data.should_show && firstMessageSent) {
        // Mostrar popup de nome após enviar primeira mensagem
        setTimeout(() => {
          setShowNamePopup(true);
        }, 2000);
      }
    } catch (error) {
      console.error('Error checking name popup:', error);
    }
  };

  const handleConfirmName = async () => {
    const name = nameInput.trim();
    if (!name) {
      toast.error('Por favor, digite seu nome');
      return;
    }
    
    // Validação no frontend também
    if (name.length < 2) {
      toast.error('Nome muito curto');
      return;
    }
    
    if (name.split(' ').length > 3) {
      toast.error('Digite apenas seu nome (máximo 3 palavras)');
      return;
    }
    
    if (!/^[A-Za-zÀ-ÿ\s]+$/.test(name)) {
      toast.error('Nome deve conter apenas letras');
      return;
    }
    
    try {
      await api.put('/users/me/name', { name });
      toast.success(`Bem-vindo(a), ${name}!`);
      setShowNamePopup(false);
      setNameInput('');
      loadTicket(); // Recarregar para atualizar nome
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar nome');
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
    
    // Habilitar áudio na primeira interação do usuário (contornar autoplay policy)
    if (!audioEnabled && notificationAudioRef.current) {
      try {
        // Tentar tocar e pausar imediatamente para "desbloquear" o áudio
        notificationAudioRef.current.volume = 0.01;
        notificationAudioRef.current.play().then(() => {
          notificationAudioRef.current.pause();
          notificationAudioRef.current.currentTime = 0;
          notificationAudioRef.current.volume = 1.0;
          setAudioEnabled(true);
          console.log('✅ Áudio habilitado após interação do usuário');
        }).catch(e => {
          console.log('⚠️ Não foi possível habilitar áudio:', e);
        });
      } catch (e) {
        console.error('Erro ao habilitar áudio:', e);
      }
    }
    
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
      
      // Marcar que enviou primeira mensagem e verificar se deve pedir nome
      if (!firstMessageSent) {
        setFirstMessageSent(true);
        setTimeout(() => {
          checkNamePopup();
        }, 2000);
      }
      
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
        {/* Header - Estilo WhatsApp */}
        <div className="bg-[#075E54] text-white p-3 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1">
              <div className="relative">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center overflow-hidden">
                  <MessageCircle className="w-5 h-5" />
                </div>
                {onlineStatus && (
                  <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-[#075E54]"></span>
                )}
              </div>
              <div className="flex-1">
                <h1 className="font-semibold text-base">Suporte</h1>
                <p className="text-xs text-white/80">
                  {onlineStatus ? 'online' : 'offline'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                data-testid="notices-btn"
                variant="ghost"
                size="icon"
                onClick={() => {
                  setShowNotices(true);
                  setHasNewNotices(false);
                  localStorage.setItem('last_notice_count', lastNoticeCount.toString());
                }}
                className={`text-white hover:bg-white/10 h-9 w-9 relative ${hasNewNotices ? 'pulse' : ''}`}
              >
                <Bell className={`w-5 h-5 ${hasNewNotices ? 'text-red-300' : ''}`} />
                {hasNewNotices && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                )}
              </Button>
              <Button
                data-testid="settings-btn"
                variant="ghost"
                size="icon"
                onClick={() => setShowSettings(true)}
                className="text-white hover:bg-white/10 h-9 w-9"
              >
                <Settings className="w-5 h-5" />
              </Button>
              <Button
                data-testid="client-logout-btn"
                variant="ghost"
                size="icon"
                onClick={() => { clearAuth(); navigate('/'); }}
                className="text-white hover:bg-white/10 h-9 w-9"
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Credentials Bar */}
        {(credentials.pinned_user || credentials.pinned_pass) && (
          <div className="bg-cyan-100 border-b border-cyan-200 px-4 py-2 text-sm">
            <span className="font-medium">Usuário:</span> {credentials.pinned_user} • 
            <span className="font-medium">Senha:</span> {credentials.pinned_pass}
          </div>
        )}

        {/* Messages - Fundo estilo WhatsApp */}
        <div 
          className="h-[500px] p-4 overflow-y-auto" 
          style={{
            backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M10 10 L90 10 L90 90 L10 90 Z\' fill=\'none\' stroke=\'%23d9d9d9\' stroke-width=\'0.5\' opacity=\'0.1\'/%3E%3C/svg%3E")',
            backgroundColor: '#e5ddd5'
          }}
        >
          <div className="space-y-3">
            {messages.map((msg, index) => {
              // Debug: log mensagem
              console.log('📝 Renderizando mensagem:', {
                id: msg.id?.substring(0, 8),
                from_type: msg.from_type,
                kind: msg.kind,
                text: msg.text?.substring(0, 50),
                has_text: !!msg.text
              });
              
              // Verificar se deve mostrar data (primeira mensagem do dia)
              const showDate = index === 0 || 
                new Date(messages[index - 1].created_at).toDateString() !== new Date(msg.created_at).toDateString();
              
              return (
              <div key={msg.id}>
                {/* Separador de data - Estilo WhatsApp */}
                {showDate && (
                  <div className="flex justify-center my-2">
                    <span className="bg-[#E1F5FE] text-gray-700 text-xs px-3 py-1 rounded-md shadow-sm">
                      {new Date(msg.created_at).toLocaleDateString('pt-BR', { 
                        day: '2-digit', 
                        month: 'long', 
                        year: 'numeric' 
                      })}
                    </span>
                  </div>
                )}
                
                <div className={`flex ${msg.from_type === 'client' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[75%] px-3 py-2 rounded-lg shadow-sm ${
                      msg.from_type === 'client'
                        ? 'bg-[#DCF8C6] text-gray-900 rounded-br-none'
                        : msg.from_type === 'ai'
                        ? 'bg-[#E1F5FE] text-gray-900 rounded-bl-none border border-blue-200'
                        : 'bg-white text-gray-900 rounded-bl-none border border-gray-200'
                    }`}
                  >
                  {/* Mostrar texto se existir */}
                  {msg.text && (
                    <p 
                      className="whitespace-pre-wrap break-words text-sm" 
                      style={{ minHeight: '20px' }}
                      dangerouslySetInnerHTML={{
                        __html: msg.text.replace(
                          /(https?:\/\/[^\s]+)/g,
                          '<a href="$1" target="_blank" rel="noopener noreferrer" class="underline text-blue-300 hover:text-blue-100">$1</a>'
                        )
                      }}
                    />
                  )}
                  
                  {/* Renderizar mídia (imagem, vídeo, áudio) */}
                  {msg.kind === 'image' && msg.file_url && (
                    <img 
                      src={msg.file_url} 
                      alt="Imagem" 
                      className="max-w-[200px] h-auto rounded-lg mt-2 cursor-pointer hover:opacity-80 transition-opacity" 
                      onClick={() => setLightboxImage(msg.file_url)}
                    />
                  )}
                  {msg.kind === 'video' && msg.file_url && (
                    <video src={msg.file_url} controls className="max-w-full rounded-lg mt-2" />
                  )}
                  {msg.kind === 'audio' && msg.file_url && (
                    <audio src={msg.file_url} controls className="w-full mt-2" />
                  )}
                  {msg.kind === 'department_selection' && (
                    <div>
                      <p className="font-semibold text-sm mb-3">{msg.text}</p>
                      <div className="space-y-2">
                        {msg.buttons && msg.buttons.map((btn, idx) => (
                          <Button
                            key={btn.id}
                            onClick={async () => {
                              try {
                                await api.post(`/tickets/${msg.ticket_id}/select-department`, {
                                  department_id: btn.id
                                });
                                toast.success(`Departamento selecionado: ${btn.label}`);
                              } catch (error) {
                                toast.error('Erro ao selecionar departamento');
                              }
                            }}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white justify-start"
                          >
                            <span className="font-bold mr-2">{idx + 1}:</span>
                            <div className="text-left">
                              <div className="font-semibold">{btn.label}</div>
                              {btn.description && (
                                <div className="text-xs opacity-80">{btn.description}</div>
                              )}
                            </div>
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.kind === 'pix' && (
                    <div className="space-y-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          const pixKey = msg.pix_key || msg.text;
                          navigator.clipboard.writeText(pixKey);
                          toast.success('Chave PIX copiada!');
                        }}
                        className="w-full bg-green-600 hover:bg-green-700 text-white"
                      >
                        💰 Copiar Chave PIX
                      </Button>
                    </div>
                  )}
                    {/* Nome e horário */}
                    <div className="flex items-center justify-between mt-1 gap-2">
                      {msg.from_type === 'client' && userData?.display_name && (
                        <span className="text-[10px] font-semibold opacity-80">
                          {userData.display_name}
                        </span>
                      )}
                      <p className="text-[10px] opacity-70 ml-auto">
                        {new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input - Estilo WhatsApp */}
        <div className="bg-[#F0F0F0] p-2 rounded-b-2xl">
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept="image/*,video/*"
              onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
            />
            <Button
              data-testid="attach-btn"
              variant="ghost"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              className="text-gray-600 hover:bg-gray-200 h-10 w-10"
            >
              <Paperclip className="w-5 h-5" />
            </Button>
            <div className="flex-1 bg-white rounded-full px-4 py-2 flex items-center gap-2">
              <Input
                data-testid="client-message-input"
                placeholder="Mensagem"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="flex-1 border-none focus:ring-0 px-0 bg-transparent"
              />
              <Button
                data-testid="record-btn"
                variant="ghost"
                size="icon"
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                className={`h-8 w-8 ${isRecording ? 'bg-red-100 text-red-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <Mic className="w-5 h-5" />
              </Button>
            </div>
            <Button 
              data-testid="send-message-btn" 
              onClick={handleSendMessage} 
              className="bg-[#075E54] hover:bg-[#064d44] h-10 w-10 rounded-full p-0"
            >
              <Send className="w-5 h-5" />
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
      
      {/* Name Confirmation Dialog */}
      <Dialog open={showNamePopup} onOpenChange={setShowNamePopup}>
        <DialogContent data-testid="name-dialog" className="max-w-md">
          <DialogHeader>
            <DialogTitle>👤 Como você gostaria de ser chamado?</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Digite seu nome para um atendimento mais personalizado:
            </p>
            <Input
              data-testid="name-input"
              placeholder="Seu nome"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleConfirmName();
                }
              }}
              autoFocus
            />
            <p className="text-xs text-slate-500">
              💡 Digite apenas seu nome (ex: João, Maria Silva)
            </p>
            <div className="flex gap-2">
              <Button
                data-testid="name-skip-btn"
                variant="outline"
                onClick={() => setShowNamePopup(false)}
                className="flex-1"
              >
                Depois
              </Button>
              <Button
                data-testid="name-confirm-btn"
                onClick={handleConfirmName}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700"
              >
                Confirmar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* PWA Install Prompt */}
      <InstallPWA />
      
      {/* Lightbox para visualizar imagens em tamanho completo */}
      {lightboxImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setLightboxImage(null)}
        >
          <div className="relative max-w-5xl max-h-full">
            <img 
              src={lightboxImage} 
              alt="Imagem ampliada" 
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setLightboxImage(null)}
              className="absolute top-4 right-4 bg-white text-black rounded-full w-10 h-10 flex items-center justify-center hover:bg-gray-200 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientChat;
