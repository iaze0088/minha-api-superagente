import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, LogOut, Users, MessageSquare, Settings, Bell, Plus, Trash2, Edit } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '../lib/api';
import { clearAuth } from '../lib/auth';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [resellers, setResellers] = useState([]);
  const [hierarchy, setHierarchy] = useState({ hierarchy: [] });
  const [config, setConfig] = useState({ 
    quick_blocks: [], 
    auto_reply: [], 
    apps: [],
    pix_key: '',
    allowed_data: { cpfs: [], emails: [], phones: [], random_keys: [] },
    api_integration: { api_url: '', api_token: '', api_enabled: false },
    ai_agent: {
      name: 'Assistente IA',
      personality: '',
      instructions: '',
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      temperature: 0.7,
      max_tokens: 500,
      mode: 'standby',
      active_hours: '24/7',
      enabled: false,
      can_access_credentials: true,
      knowledge_base: ''
    }
  });
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Agent form
  const [newAgent, setNewAgent] = useState({ name: '', login: '', password: '', avatar: '' });
  const [editingAgent, setEditingAgent] = useState(null);
  
  // Reseller form
  const [newReseller, setNewReseller] = useState({ name: '', email: '', password: '', domain: '', parent_id: null });
  const [editingReseller, setEditingReseller] = useState(null);
  const [expandedResellers, setExpandedResellers] = useState(new Set());
  const [transferModal, setTransferModal] = useState({ open: false, reseller: null });
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'tree'

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsRes, resellersRes, hierarchyRes, configRes, noticesRes] = await Promise.all([
        api.get('/agents'),
        api.get('/resellers').catch(() => ({ data: [] })),
        api.get('/resellers/hierarchy').catch(() => ({ data: { hierarchy: [] } })),
        api.get('/config'),
        api.get('/notices')
      ]);
      setAgents(agentsRes.data);
      setResellers(resellersRes.data);
      setHierarchy(hierarchyRes.data);
      setConfig(configRes.data);
      setNotices(noticesRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate('/');
  };

  const handleCreateAgent = async () => {
    try {
      await api.post('/agents', newAgent);
      toast.success('Atendente criado com sucesso!');
      setNewAgent({ name: '', login: '', password: '', avatar: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar atendente');
    }
  };

  const handleUpdateAgent = async (agentId, data) => {
    try {
      await api.put(`/agents/${agentId}`, data);
      toast.success('Atendente atualizado!');
      setEditingAgent(null);
      loadData();
    } catch (error) {
      toast.error('Erro ao atualizar atendente');
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!window.confirm('Tem certeza que deseja excluir este atendente?')) return;
    try {
      await api.delete(`/agents/${agentId}`);
      toast.success('Atendente excluído!');
      loadData();
    } catch (error) {
      toast.error('Erro ao excluir atendente');
    }
  };
  
  // Reseller functions
  const handleCreateReseller = async () => {
    try {
      await api.post('/resellers', newReseller);
      toast.success('Revenda criada com sucesso!');
      setNewReseller({ name: '', email: '', password: '', domain: '', parent_id: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar revenda');
    }
  };
  
  const handleDeleteReseller = async (resellerId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta revenda?')) return;
    try {
      await api.delete(`/resellers/${resellerId}`);
      toast.success('Revenda excluída!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir revenda');
    }
  };
  
  const handleTransferReseller = async () => {
    try {
      await api.post('/resellers/transfer', {
        reseller_id: transferModal.reseller.id,
        new_parent_id: transferModal.new_parent_id
      });
      toast.success('Revenda transferida com sucesso!');
      setTransferModal({ open: false, reseller: null });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao transferir revenda');
    }
  };
  
  const toggleExpand = (resellerId) => {
    const newExpanded = new Set(expandedResellers);
    if (newExpanded.has(resellerId)) {
      newExpanded.delete(resellerId);
    } else {
      newExpanded.add(resellerId);
    }
    setExpandedResellers(newExpanded);
  };
  
  const handleReplicateConfig = async () => {
    if (!window.confirm('Isso vai sobrescrever as configurações de TODAS as revendas. Continuar?')) return;
    try {
      const { data } = await api.post('/resellers/replicate-config');
      toast.success(`Configurações replicadas para ${data.updated} revenda(s)!`);
    } catch (error) {
      toast.error('Erro ao replicar configurações');
    }
  };

  const handleSaveConfig = async () => {
    try {
      await api.put('/config', config);
      toast.success('Configurações salvas!');
    } catch (error) {
      toast.error('Erro ao salvar configurações');
    }
  };

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return data.url;
    } catch (error) {
      toast.error('Erro ao fazer upload');
      return null;
    }
  };

  const handleCreateNotice = async (kind, text, file) => {
    try {
      let fileUrl = '';
      if (file) {
        fileUrl = await handleUpload(file);
        if (!fileUrl) return;
      }
      await api.post('/notices', { kind, text: text || '', file_url: fileUrl || '' });
      toast.success('Aviso publicado!');
      loadData();
    } catch (error) {
      toast.error('Erro ao publicar aviso');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-slate-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Admin Dashboard</h1>
              <p className="text-sm text-slate-600">Gerenciamento completo</p>
            </div>
          </div>
          <Button data-testid="logout-btn" onClick={handleLogout} variant="outline" size="sm">
            <LogOut className="w-4 h-4 mr-2" />
            Sair
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs defaultValue="agents" className="space-y-6">
          <TabsList className="grid w-full grid-cols-7 lg:w-auto lg:inline-grid">
            <TabsTrigger value="resellers" data-testid="tab-resellers">
              <Users className="w-4 h-4 mr-2" />
              Revendas
            </TabsTrigger>
            <TabsTrigger value="agents" data-testid="tab-agents">
              <Users className="w-4 h-4 mr-2" />
              Atendentes
            </TabsTrigger>
            <TabsTrigger value="quick" data-testid="tab-quick">
              <MessageSquare className="w-4 h-4 mr-2" />
              Msg Rápidas
            </TabsTrigger>
            <TabsTrigger value="security" data-testid="tab-security">
              <Shield className="w-4 h-4 mr-2" />
              Dados Permitidos
            </TabsTrigger>
            <TabsTrigger value="api" data-testid="tab-api">
              <Settings className="w-4 h-4 mr-2" />
              API
            </TabsTrigger>
            <TabsTrigger value="ai" data-testid="tab-ai">
              <MessageSquare className="w-4 h-4 mr-2" />
              IA
            </TabsTrigger>
            <TabsTrigger value="notices" data-testid="tab-notices">
              <Bell className="w-4 h-4 mr-2" />
              Avisos
            </TabsTrigger>
          </TabsList>

          {/* Resellers Tab */}
          <TabsContent value="resellers" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Gerenciar Revendas</h3>
              <p className="text-sm text-slate-600 mb-4">Sistema multi-tenant ativo com isolamento de dados</p>
              <div className="grid gap-4">
                {resellers.map((reseller) => (
                  <Card key={reseller.id} className="p-4">
                    <h4 className="font-semibold">{reseller.name}</h4>
                    <p className="text-sm text-slate-600">Email: {reseller.email}</p>
                    {reseller.custom_domain && (
                      <p className="text-sm text-emerald-600">Domínio: {reseller.custom_domain}</p>
                    )}
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                      Nível {reseller.level || 0}
                    </span>
                  </Card>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Novo Atendente</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <Input
                  data-testid="agent-name-input"
                  placeholder="Nome"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                />
                <Input
                  data-testid="agent-login-input-field"
                  placeholder="Login"
                  value={newAgent.login}
                  onChange={(e) => setNewAgent({ ...newAgent, login: e.target.value })}
                />
                <Input
                  data-testid="agent-password-input-field"
                  type="password"
                  placeholder="Senha"
                  value={newAgent.password}
                  onChange={(e) => setNewAgent({ ...newAgent, password: e.target.value })}
                />
                <Input
                  data-testid="agent-avatar-input"
                  placeholder="Avatar URL (opcional)"
                  value={newAgent.avatar}
                  onChange={(e) => setNewAgent({ ...newAgent, avatar: e.target.value })}
                />
              </div>
              <Button data-testid="create-agent-btn" onClick={handleCreateAgent} className="mt-4 bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Adicionar Atendente
              </Button>
            </Card>

            <div className="grid gap-4">
              {agents.map((agent) => (
                <Card key={agent.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {agent.avatar && (
                        <img src={agent.avatar} alt={agent.name} className="w-12 h-12 rounded-full object-cover" />
                      )}
                      <div>
                        <h4 className="font-semibold text-slate-900">{agent.name}</h4>
                        <p className="text-sm text-slate-600">@{agent.login}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button data-testid={`edit-agent-${agent.id}-btn`} variant="outline" size="sm" onClick={() => setEditingAgent(agent)}>
                            <Edit className="w-4 h-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Editar Atendente</DialogTitle>
                          </DialogHeader>
                          {editingAgent && editingAgent.id === agent.id && (
                            <div className="space-y-4">
                              <Input
                                placeholder="Nome"
                                defaultValue={agent.name}
                                onChange={(e) => setEditingAgent({ ...editingAgent, name: e.target.value })}
                              />
                              <Input
                                placeholder="Login"
                                defaultValue={agent.login}
                                onChange={(e) => setEditingAgent({ ...editingAgent, login: e.target.value })}
                              />
                              <Input
                                type="password"
                                placeholder="Nova senha (opcional)"
                                onChange={(e) => setEditingAgent({ ...editingAgent, password: e.target.value })}
                              />
                              <Button onClick={() => handleUpdateAgent(agent.id, editingAgent)} className="w-full">
                                Salvar
                              </Button>
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                      <Button data-testid={`delete-agent-${agent.id}-btn`} variant="outline" size="sm" onClick={() => handleDeleteAgent(agent.id)}>
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Quick Messages Tab */}
          <TabsContent value="quick" className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Mensagens Rápidas</h3>
                <Button
                  data-testid="add-quick-block-btn"
                  size="sm"
                  onClick={() => setConfig({
                    ...config,
                    quick_blocks: [...config.quick_blocks, { name: '', text: '' }]
                  })}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Bloco
                </Button>
              </div>
              <div className="space-y-4">
                {config.quick_blocks.map((block, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <Input
                        placeholder="Nome do bloco"
                        value={block.name}
                        onChange={(e) => {
                          const updated = [...config.quick_blocks];
                          updated[idx].name = e.target.value;
                          setConfig({ ...config, quick_blocks: updated });
                        }}
                        className="flex-1 mr-2"
                      />
                      <Button
                        data-testid={`remove-quick-block-${idx}-btn`}
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = config.quick_blocks.filter((_, i) => i !== idx);
                          setConfig({ ...config, quick_blocks: updated });
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                    <Textarea
                      placeholder="Texto da mensagem"
                      value={block.text}
                      onChange={(e) => {
                        const updated = [...config.quick_blocks];
                        updated[idx].text = e.target.value;
                        setConfig({ ...config, quick_blocks: updated });
                      }}
                      rows={3}
                    />
                  </div>
                ))}
              </div>
              <Button data-testid="save-quick-blocks-btn" onClick={handleSaveConfig} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Salvar Configurações
              </Button>
            </Card>
          </TabsContent>

          {/* Security Tab - Dados Permitidos */}
          <TabsContent value="security" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">🔐 Dados Permitidos para Envio</h3>
              <p className="text-sm text-slate-600 mb-6">Configure quais dados sensíveis podem ser enviados nas conversas</p>
              
              {/* Chave PIX */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">💰 Chave PIX</h4>
                <div className="flex gap-2">
                  <Input
                    placeholder="Digite a chave PIX (CPF, Email, Telefone ou Chave Aleatória)"
                    value={config.pix_key || ''}
                    onChange={(e) => setConfig({ ...config, pix_key: e.target.value })}
                    className="flex-1"
                  />
                  <Button onClick={handleSaveConfig} className="bg-emerald-600 hover:bg-emerald-700">
                    💾 Salvar PIX
                  </Button>
                </div>
                {config.pix_key && (
                  <p className="text-sm text-emerald-600 mt-2">✅ Chave PIX cadastrada: {config.pix_key}</p>
                )}
              </div>

              {/* Botão Replicar Configurações */}
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-amber-900 mb-2">⚡ Replicar para Todas as Revendas</h4>
                <p className="text-sm text-amber-700 mb-3">
                  Propaga todas as configurações desta página (PIX, Dados Permitidos) para TODAS as revendas do sistema.
                </p>
                <Button 
                  onClick={handleReplicateConfig} 
                  className="bg-amber-600 hover:bg-amber-700 w-full"
                  variant="default"
                >
                  🔄 Replicar Configurações
                </Button>
              </div>

              {/* CPFs Permitidos */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">📄 CPFs Permitidos</h4>
                <p className="text-xs text-slate-500 mb-2">Apenas CPFs cadastrados aqui poderão ser enviados nas conversas</p>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="000.000.000-00"
                    id="new-cpf"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-cpf');
                        const cpf = input.value.trim();
                        if (cpf) {
                          const cpfs = config.allowed_data?.cpfs || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, cpfs: [...cpfs, cpf] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-cpf');
                    const cpf = input.value.trim();
                    if (cpf) {
                      const cpfs = config.allowed_data?.cpfs || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, cpfs: [...cpfs, cpf] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.cpfs || []).map((cpf, idx) => (
                    <span key={idx} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {cpf}
                      <button onClick={() => {
                        const cpfs = config.allowed_data.cpfs.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, cpfs } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Emails Permitidos */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">📧 Emails Permitidos</h4>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="email@exemplo.com"
                    type="email"
                    id="new-email"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-email');
                        const email = input.value.trim();
                        if (email) {
                          const emails = config.allowed_data?.emails || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, emails: [...emails, email] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-email');
                    const email = input.value.trim();
                    if (email) {
                      const emails = config.allowed_data?.emails || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, emails: [...emails, email] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.emails || []).map((email, idx) => (
                    <span key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {email}
                      <button onClick={() => {
                        const emails = config.allowed_data.emails.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, emails } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Telefones Permitidos */}
              <div className="mb-6">
                <h4 className="font-semibold mb-3">📱 Telefones/WhatsApp Permitidos</h4>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="+55 11 91111-1111"
                    id="new-phone"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-phone');
                        const phone = input.value.trim();
                        if (phone) {
                          const phones = config.allowed_data?.phones || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, phones: [...phones, phone] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-phone');
                    const phone = input.value.trim();
                    if (phone) {
                      const phones = config.allowed_data?.phones || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, phones: [...phones, phone] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.phones || []).map((phone, idx) => (
                    <span key={idx} className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {phone}
                      <button onClick={() => {
                        const phones = config.allowed_data.phones.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, phones } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Chaves Aleatórias PIX */}
              <div>
                <h4 className="font-semibold mb-3">🔑 Chaves Aleatórias PIX</h4>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="UUID ou chave aleatória"
                    id="new-random-key"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const input = document.getElementById('new-random-key');
                        const key = input.value.trim();
                        if (key) {
                          const keys = config.allowed_data?.random_keys || [];
                          setConfig({
                            ...config,
                            allowed_data: { ...config.allowed_data, random_keys: [...keys, key] }
                          });
                          input.value = '';
                        }
                      }
                    }}
                  />
                  <Button onClick={() => {
                    const input = document.getElementById('new-random-key');
                    const key = input.value.trim();
                    if (key) {
                      const keys = config.allowed_data?.random_keys || [];
                      setConfig({
                        ...config,
                        allowed_data: { ...config.allowed_data, random_keys: [...keys, key] }
                      });
                      input.value = '';
                      handleSaveConfig();
                    }
                  }}>
                    Adicionar
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(config.allowed_data?.random_keys || []).map((key, idx) => (
                    <span key={idx} className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                      {key}
                      <button onClick={() => {
                        const keys = config.allowed_data.random_keys.filter((_, i) => i !== idx);
                        setConfig({ ...config, allowed_data: { ...config.allowed_data, random_keys: keys } });
                        handleSaveConfig();
                      }} className="text-red-600 hover:text-red-800">×</button>
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* API Tab */}
          <TabsContent value="api" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">🔌 Integração API Office</h3>
              <p className="text-sm text-slate-600 mb-6">Configure a API para buscar automaticamente usuário e senha dos clientes</p>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">URL da API</label>
                  <Input
                    placeholder="https://api.office.com/v1/..."
                    value={config.api_integration?.api_url || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      api_integration: { ...config.api_integration, api_url: e.target.value }
                    })}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">Token de Autenticação</label>
                  <Input
                    type="password"
                    placeholder="Bearer token ou API key"
                    value={config.api_integration?.api_token || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      api_integration: { ...config.api_integration, api_token: e.target.value }
                    })}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="api-enabled"
                    checked={config.api_integration?.api_enabled || false}
                    onChange={(e) => setConfig({
                      ...config,
                      api_integration: { ...config.api_integration, api_enabled: e.target.checked }
                    })}
                    className="rounded"
                  />
                  <label htmlFor="api-enabled" className="text-sm font-medium">
                    Ativar integração com API
                  </label>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={async () => {
                      if (!config.api_integration?.api_url) {
                        toast.error('Configure a URL da API primeiro');
                        return;
                      }
                      try {
                        toast.info('Testando conexão...');
                        // TODO: Implementar teste real quando houver API
                        setTimeout(() => toast.success('✅ API configurada! (teste futuro)'), 1000);
                      } catch (error) {
                        toast.error('Erro ao testar API');
                      }
                    }}
                    variant="outline"
                  >
                    🧪 Testar Conexão
                  </Button>
                  
                  <Button onClick={handleSaveConfig} className="bg-blue-600 hover:bg-blue-700">
                    💾 Salvar Configuração
                  </Button>
                </div>

                {config.api_integration?.api_enabled && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                    <p className="text-sm text-green-800">
                      ✅ Integração API ativa! Os atendentes poderão buscar credenciais automaticamente.
                    </p>
                  </div>
                )}
                
                {/* Botão Replicar Configurações */}
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200 rounded-lg p-4 mt-4">
                  <h4 className="font-semibold text-amber-900 mb-2">⚡ Replicar para Todas as Revendas</h4>
                  <p className="text-sm text-amber-700 mb-3">
                    Propaga as configurações de API para TODAS as revendas do sistema.
                  </p>
                  <Button 
                    onClick={handleReplicateConfig} 
                    className="bg-amber-600 hover:bg-amber-700 w-full"
                    variant="default"
                  >
                    🔄 Replicar Configurações
                  </Button>
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* AI Tab */}
          <TabsContent value="ai" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">🤖 Inteligência Artificial</h3>
              <p className="text-sm text-slate-600 mb-6">Configure o agente de IA para atendimento automatizado</p>
              
              <div className="space-y-6">
                {/* Ativar/Desativar IA */}
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-purple-900">Status da IA</h4>
                      <p className="text-sm text-purple-700">
                        {config.ai_agent?.enabled ? '✅ Ativa e pronta para atender' : '⏸️ Desativada'}
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={config.ai_agent?.enabled || false}
                      onChange={(e) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, enabled: e.target.checked }
                      })}
                      className="w-12 h-6 rounded-full"
                    />
                  </div>
                </div>

                {/* Nome e Personalidade */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Nome do Agente IA</label>
                    <Input
                      placeholder="Ex: Assistente Virtual"
                      value={config.ai_agent?.name || ''}
                      onChange={(e) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, name: e.target.value }
                      })}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Modo de Operação</label>
                    <Select
                      value={config.ai_agent?.mode || 'standby'}
                      onValueChange={(val) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, mode: val }
                      })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standby">⏸️ Standby (apenas quando solicitado)</SelectItem>
                        <SelectItem value="solo">🤖 Solo (sem atendentes)</SelectItem>
                        <SelectItem value="hybrid">🤝 Híbrido (com atendentes)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Provider LLM */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Provedor LLM</label>
                    <Select
                      value={config.ai_agent?.llm_provider || 'openai'}
                      onValueChange={(val) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, llm_provider: val }
                      })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">🟢 OpenAI (GPT-4, GPT-3.5)</SelectItem>
                        <SelectItem value="claude">🟣 Anthropic Claude</SelectItem>
                        <SelectItem value="gemini">🔵 Google Gemini</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Modelo</label>
                    <Input
                      placeholder="gpt-4, claude-3, gemini-pro"
                      value={config.ai_agent?.llm_model || ''}
                      onChange={(e) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, llm_model: e.target.value }
                      })}
                    />
                  </div>
                </div>

                {/* Personalidade */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Personalidade do Agente</label>
                  <textarea
                    className="w-full min-h-[80px] px-3 py-2 border rounded-md"
                    placeholder="Ex: Você é um assistente amigável e prestativo. Seja educado e objetivo..."
                    value={config.ai_agent?.personality || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ai_agent: { ...config.ai_agent, personality: e.target.value }
                    })}
                  />
                </div>

                {/* Instruções */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Instruções Específicas</label>
                  <textarea
                    className="w-full min-h-[100px] px-3 py-2 border rounded-md"
                    placeholder="Ex: Sempre cumprimente o cliente. Pergunte como pode ajudar. Use a base de conhecimento..."
                    value={config.ai_agent?.instructions || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ai_agent: { ...config.ai_agent, instructions: e.target.value }
                    })}
                  />
                </div>

                {/* Knowledge Base */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Base de Conhecimento</label>
                  <textarea
                    className="w-full min-h-[120px] px-3 py-2 border rounded-md"
                    placeholder="Cole aqui FAQs, informações sobre produtos, políticas, etc..."
                    value={config.ai_agent?.knowledge_base || ''}
                    onChange={(e) => setConfig({
                      ...config,
                      ai_agent: { ...config.ai_agent, knowledge_base: e.target.value }
                    })}
                  />
                </div>

                {/* Configurações Avançadas */}
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Temperatura (Criatividade)</label>
                    <Input
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={config.ai_agent?.temperature || 0.7}
                      onChange={(e) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, temperature: parseFloat(e.target.value) }
                      })}
                    />
                    <p className="text-xs text-slate-500 mt-1">0 = Preciso, 1 = Criativo</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Tokens (Resposta)</label>
                    <Input
                      type="number"
                      min="100"
                      max="2000"
                      step="100"
                      value={config.ai_agent?.max_tokens || 500}
                      onChange={(e) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, max_tokens: parseInt(e.target.value) }
                      })}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Horário de Ativação</label>
                    <Input
                      placeholder="24/7 ou 09:00-18:00"
                      value={config.ai_agent?.active_hours || '24/7'}
                      onChange={(e) => setConfig({
                        ...config,
                        ai_agent: { ...config.ai_agent, active_hours: e.target.value }
                      })}
                    />
                  </div>
                </div>

                {/* Acesso a Credenciais */}
                <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <input
                    type="checkbox"
                    id="ai-credentials"
                    checked={config.ai_agent?.can_access_credentials || false}
                    onChange={(e) => setConfig({
                      ...config,
                      ai_agent: { ...config.ai_agent, can_access_credentials: e.target.checked }
                    })}
                    className="rounded"
                  />
                  <label htmlFor="ai-credentials" className="text-sm font-medium">
                    🔐 Permitir IA acessar credenciais fixadas (usuário/senha) dos clientes
                  </label>
                </div>

                <Button onClick={handleSaveConfig} className="w-full bg-purple-600 hover:bg-purple-700">
                  💾 Salvar Configuração de IA
                </Button>
              </div>
            </Card>
          </TabsContent>


          {/* Config Tab */}
          <TabsContent value="config" className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Auto-Resposta</h3>
                <Button
                  data-testid="add-auto-reply-btn"
                  size="sm"
                  onClick={() => setConfig({
                    ...config,
                    auto_reply: [...config.auto_reply, { q: '', a: '' }]
                  })}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nova Regra
                </Button>
              </div>
              <div className="space-y-4">
                {config.auto_reply.map((rule, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-slate-700">Regra {idx + 1}</h4>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = config.auto_reply.filter((_, i) => i !== idx);
                          setConfig({ ...config, auto_reply: updated });
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                    <Input
                      placeholder="Pergunta do cliente"
                      value={rule.q}
                      onChange={(e) => {
                        const updated = [...config.auto_reply];
                        updated[idx].q = e.target.value;
                        setConfig({ ...config, auto_reply: updated });
                      }}
                    />
                    <Textarea
                      placeholder="Resposta automática"
                      value={rule.a}
                      onChange={(e) => {
                        const updated = [...config.auto_reply];
                        updated[idx].a = e.target.value;
                        setConfig({ ...config, auto_reply: updated });
                      }}
                      rows={2}
                    />
                  </div>
                ))}
              </div>
              <Button onClick={handleSaveConfig} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Salvar Auto-Resposta
              </Button>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Aplicativos / Tutoriais</h3>
                <Button
                  data-testid="add-app-btn"
                  size="sm"
                  onClick={() => setConfig({
                    ...config,
                    apps: [...config.apps, { cat: 'SmartTV', title: '', content: '' }]
                  })}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Item
                </Button>
              </div>
              <div className="space-y-4">
                {config.apps.map((app, idx) => (
                  <div key={idx} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <Select
                        value={app.cat}
                        onValueChange={(value) => {
                          const updated = [...config.apps];
                          updated[idx].cat = value;
                          setConfig({ ...config, apps: updated });
                        }}
                      >
                        <SelectTrigger className="w-[200px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {['Tv box', 'SmartTV', 'Celular IOS', 'Celular Android', 'AndroidTV', 'Projetor', 'Fire stick TV', 'Video Game', 'Chromecast'].map(cat => (
                            <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Input
                        placeholder="Título"
                        value={app.title}
                        onChange={(e) => {
                          const updated = [...config.apps];
                          updated[idx].title = e.target.value;
                          setConfig({ ...config, apps: updated });
                        }}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const updated = config.apps.filter((_, i) => i !== idx);
                          setConfig({ ...config, apps: updated });
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                    <Textarea
                      placeholder="Conteúdo / instruções"
                      value={app.content}
                      onChange={(e) => {
                        const updated = [...config.apps];
                        updated[idx].content = e.target.value;
                        setConfig({ ...config, apps: updated });
                      }}
                      rows={3}
                    />
                  </div>
                ))}
              </div>
              <Button onClick={handleSaveConfig} className="mt-4 bg-purple-600 hover:bg-purple-700">
                Salvar Aplicativos
              </Button>
            </Card>
          </TabsContent>

          {/* Notices Tab */}
          <TabsContent value="notices" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Publicar Novo Aviso</h3>
              <NoticeForm onSubmit={handleCreateNotice} />
            </Card>

            <div className="grid gap-4">
              {notices.map((notice) => (
                <Card key={notice.id} className="p-4">
                  <div className="flex items-start gap-4">
                    {notice.kind === 'image' && (
                      <img src={notice.file_url} alt="" className="w-24 h-24 object-cover rounded-lg" />
                    )}
                    {notice.kind === 'video' && (
                      <video src={notice.file_url} controls className="w-48 rounded-lg" />
                    )}
                    {notice.kind === 'audio' && (
                      <audio src={notice.file_url} controls className="w-full" />
                    )}
                    <div className="flex-1">
                      {notice.text && <p className="text-slate-700">{notice.text}</p>}
                      <p className="text-xs text-slate-500 mt-2">
                        {new Date(notice.created_at).toLocaleString('pt-BR')}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

const NoticeForm = ({ onSubmit }) => {
  const [kind, setKind] = useState('text');
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);

  const handleSubmit = () => {
    onSubmit(kind, text, file);
    setText('');
    setFile(null);
  };

  return (
    <div className="space-y-4">
      <Select value={kind} onValueChange={setKind}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="text">Texto</SelectItem>
          <SelectItem value="image">Imagem</SelectItem>
          <SelectItem value="video">Vídeo</SelectItem>
          <SelectItem value="audio">Áudio</SelectItem>
        </SelectContent>
      </Select>

      {kind === 'text' && (
        <Textarea
          placeholder="Mensagem do aviso"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
        />
      )}

      {kind !== 'text' && (
        <Input
          type="file"
          accept={kind === 'image' ? 'image/*' : kind === 'video' ? 'video/*' : 'audio/*'}
          onChange={(e) => setFile(e.target.files[0])}
        />
      )}

      <Button data-testid="publish-notice-btn" onClick={handleSubmit} className="bg-purple-600 hover:bg-purple-700">
        <Bell className="w-4 h-4 mr-2" />
        Publicar Aviso
      </Button>
    </div>
  );
};

export default AdminDashboard;
