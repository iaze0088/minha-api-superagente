import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, LogOut, Users, MessageSquare, Settings, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '../lib/api';
import { clearAuth, getAuth } from '../lib/auth';
import ResellerDomainManager from '../components/ResellerDomainManager';
import FirstLoginPasswordChange from '../components/FirstLoginPasswordChange';
import DNSReminderPopup from '../components/DNSReminderPopup';

const ResellerDashboard = () => {
  const navigate = useNavigate();
  const { userData } = getAuth();
  const [config, setConfig] = useState({ quick_blocks: [], auto_reply: [], apps: [] });
  const [agents, setAgents] = useState([]);
  const [newAgent, setNewAgent] = useState({ name: '', login: '', password: '', avatar: '' });
  const [loading, setLoading] = useState(true);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [resellerInfo, setResellerInfo] = useState(null);

  useEffect(() => {
    checkFirstLogin();
    loadData();
  }, []);

  const checkFirstLogin = async () => {
    try {
      const { data } = await api.get('/reseller/me');
      setResellerInfo(data);
      
      if (data.first_login) {
        setShowPasswordChange(true);
      }
    } catch (error) {
      console.error('Erro ao verificar primeiro login:', error);
    }
  };

  const handlePasswordChangeSuccess = () => {
    setShowPasswordChange(false);
    toast.success('✅ Senha alterada com sucesso!');
    checkFirstLogin(); // Recarregar info
  };

  const loadData = async () => {
    try {
      const [configRes, agentsRes] = await Promise.all([
        api.get('/config'),
        api.get('/agents')
      ]);
      setConfig(configRes.data);
      setAgents(agentsRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      await api.put(`/resellers/${userData.id}/config`, config);
      toast.success('Configurações salvas!');
    } catch (error) {
      toast.error('Erro ao salvar configurações');
    }
  };

  const handleCreateAgent = async () => {
    try {
      await api.post('/agents', newAgent);
      toast.success('Atendente criado!');
      setNewAgent({ name: '', login: '', password: '', avatar: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar atendente');
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

  const handleLogout = () => {
    clearAuth();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-slate-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Modal de troca de senha no primeiro login */}
      <FirstLoginPasswordChange 
        isOpen={showPasswordChange} 
        onSuccess={handlePasswordChangeSuccess}
      />

      {/* Pop-up de lembrete DNS (24h) */}
      <DNSReminderPopup resellerData={resellerInfo} />

      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center">
              <Store className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Painel Revenda</h1>
              <p className="text-sm text-slate-600">{userData?.name}</p>
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
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="agents" data-testid="tab-agents">
              <Users className="w-4 h-4 mr-2" />
              Atendentes
            </TabsTrigger>
            <TabsTrigger value="quick" data-testid="tab-quick">
              <MessageSquare className="w-4 h-4 mr-2" />
              Msg Rápidas
            </TabsTrigger>
            <TabsTrigger value="config" data-testid="tab-config">
              <Settings className="w-4 h-4 mr-2" />
              Configurações
            </TabsTrigger>
            <TabsTrigger value="domain" data-testid="tab-domain">
              <Settings className="w-4 h-4 mr-2" />
              Domínio
            </TabsTrigger>
          </TabsList>

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Novo Atendente</h3>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <Input
                  placeholder="Nome"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                />
                <Input
                  placeholder="Login"
                  value={newAgent.login}
                  onChange={(e) => setNewAgent({ ...newAgent, login: e.target.value })}
                />
                <Input
                  type="password"
                  placeholder="Senha"
                  value={newAgent.password}
                  onChange={(e) => setNewAgent({ ...newAgent, password: e.target.value })}
                />
                <Select value={newAgent.avatar} onValueChange={(val) => setNewAgent({ ...newAgent, avatar: val })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Avatar" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="👨">👨 Homem</SelectItem>
                    <SelectItem value="👩">👩 Mulher</SelectItem>
                    <SelectItem value="🧑">🧑 Pessoa</SelectItem>
                    <SelectItem value="👤">👤 Perfil</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={handleCreateAgent} className="bg-emerald-600 hover:bg-emerald-700">
                <Plus className="w-4 h-4 mr-2" />
                Criar Atendente
              </Button>
            </Card>

            <div className="grid gap-4">
              {agents.map((agent) => (
                <Card key={agent.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{agent.avatar}</div>
                      <div>
                        <h4 className="font-semibold">{agent.name}</h4>
                        <p className="text-sm text-slate-600">Login: {agent.login}</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteAgent(agent.id)}
                      className="text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))}
              {agents.length === 0 && (
                <Card className="p-8 text-center">
                  <Users className="w-16 h-16 mx-auto text-slate-300 mb-4" />
                  <p className="text-slate-600">Nenhum atendente criado</p>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="quick" className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Mensagens Rápidas</h3>
                <Button
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
              <Button onClick={handleSaveConfig} className="mt-4 bg-emerald-600 hover:bg-emerald-700">
                Salvar Configurações
              </Button>
            </Card>
          </TabsContent>

          <TabsContent value="config" className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Auto-Resposta</h3>
                <Button
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
              <Button onClick={handleSaveConfig} className="mt-4 bg-emerald-600 hover:bg-emerald-700">
                Salvar Auto-Resposta
              </Button>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Aplicativos / Tutoriais</h3>
                <Button
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
              <Button onClick={handleSaveConfig} className="mt-4 bg-emerald-600 hover:bg-emerald-700">
                Salvar Aplicativos
              </Button>
            </Card>
          </TabsContent>

          <TabsContent value="domain" className="space-y-6">
            <ResellerDomainManager />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ResellerDashboard;
