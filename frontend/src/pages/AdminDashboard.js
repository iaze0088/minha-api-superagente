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
  const [config, setConfig] = useState({ quick_blocks: [], auto_reply: [], apps: [] });
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
