import React, { useState, useEffect } from 'react';
import { Plus, Bot, Edit, Trash2, Power, PowerOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';
import { toast } from 'sonner';

const AIAgentsManager = () => {
  const [agents, setAgents] = useState([]);
  const [allAgentsUsers, setAllAgentsUsers] = useState([]); // Lista de atendentes disponíveis
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showLinkAgentsDialog, setShowLinkAgentsDialog] = useState(false);
  const [agentToLink, setAgentToLink] = useState(null);
  const [selectedAgentsUsers, setSelectedAgentsUsers] = useState([]);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentDesc, setNewAgentDesc] = useState('');

  useEffect(() => {
    loadAgents();
    loadAllAgentsUsers();
  }, []);
  
  const loadAllAgentsUsers = async () => {
    try {
      const { data } = await api.get('/agents');
      setAllAgentsUsers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading agents users:', error);
      setAllAgentsUsers([]);
    }
  };

  const loadAgents = async () => {
    try {
      const { data } = await api.get('/ai/agents');
      setAgents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading agents:', error);
      setAgents([]);
      toast.error('Erro ao carregar agentes');
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgentName.trim()) {
      toast.error('Digite um nome para o agente');
      return;
    }

    try {
      await api.post('/ai/agents', {
        name: newAgentName,
        description: newAgentDesc,
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini'
      });
      toast.success('Agente criado com sucesso!');
      setShowCreateDialog(false);
      setNewAgentName('');
      setNewAgentDesc('');
      loadAgents();
    } catch (error) {
      toast.error('Erro ao criar agente');
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!confirm('Tem certeza que deseja deletar este agente?')) return;

    try {
      await api.delete(`/ai/agents/${agentId}`);
      toast.success('Agente deletado!');
      loadAgents();
    } catch (error) {
      toast.error('Erro ao deletar agente');
    }
  };

  const handleToggleActive = async (agent) => {
    // Abrir diálogo para selecionar atendentes
    setAgentToLink(agent);
    setSelectedAgentsUsers(agent.linked_agents || []);
    setShowLinkAgentsDialog(true);
  };
  
  const handleSaveLinkAgents = async () => {
    try {
      await api.put(`/ai/agents/${agentToLink.id}`, {
        is_active: selectedAgentsUsers.length > 0, // Ativo se tiver atendentes vinculados
        linked_agents: selectedAgentsUsers
      });
      toast.success('Atendentes vinculados com sucesso!');
      setShowLinkAgentsDialog(false);
      loadAgents();
    } catch (error) {
      toast.error('Erro ao vincular atendentes');
    }
  };
  
  const toggleAgentUser = (agentUserId) => {
    setSelectedAgentsUsers(prev => 
      prev.includes(agentUserId) 
        ? prev.filter(id => id !== agentUserId)
        : [...prev, agentUserId]
    );
  };

  return (
    <>
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">🤖 Explore os Super Agentes</h2>
        <p className="text-slate-600 mb-4">Crie os seus Super Agentes</p>
        <p className="text-sm text-slate-500 mb-6">Gerencie seus agentes para automatizar tarefas de forma inteligente.</p>
        
        <Button 
          onClick={() => setShowCreateDialog(true)}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo agente +
        </Button>
      </div>

      {/* Lista de Agentes */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(agents || []).map(agent => (
          <Card 
            key={agent.id}
            className="p-4 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  agent.is_active ? 'bg-indigo-100' : 'bg-slate-100'
                }`}>
                  <Bot className={`w-5 h-5 ${agent.is_active ? 'text-indigo-600' : 'text-slate-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{agent.name}</h3>
                  <p className="text-xs text-slate-500">{agent.llm_model}</p>
                </div>
              </div>
              
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleActive(agent);
                  }}
                  title={agent.is_active ? 'Desativar' : 'Ativar'}
                >
                  {agent.is_active ? (
                    <Power className="w-4 h-4 text-green-600" />
                  ) : (
                    <PowerOff className="w-4 h-4 text-slate-400" />
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAgent(agent);
                    setShowConfigDialog(true);
                  }}
                >
                  <Edit className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteAgent(agent.id);
                  }}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            </div>
            
            <p className="text-sm text-slate-600 mb-2">{agent.description || 'Sem descrição'}</p>
            
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>{agent.llm_provider}</span>
              <span className={`px-2 py-1 rounded ${
                agent.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
              }`}>
                {agent.is_active ? 'Ativo' : 'Inativo'}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Dialog: Criar Novo Agente */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Criar Novo Agente IA</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Nome do Agente</label>
              <Input
                placeholder="Ex: Agente de Suporte"
                value={newAgentName}
                onChange={(e) => setNewAgentName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Descrição</label>
              <Textarea
                placeholder="O que este agente faz?"
                value={newAgentDesc}
                onChange={(e) => setNewAgentDesc(e.target.value)}
                rows={3}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleCreateAgent} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
                Criar Agente
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog: Configurar Agente */}
      {selectedAgent && (
        <AgentConfigDialog
          agent={selectedAgent}
          open={showConfigDialog}
          onClose={() => {
            setShowConfigDialog(false);
            setSelectedAgent(null);
            loadAgents();
          }}
        />
      )}
      
      {/* Dialog para vincular atendentes */}
      <Dialog open={showLinkAgentsDialog} onOpenChange={setShowLinkAgentsDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>⚡ Ativar/Desativar Agente IA</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                <strong>Agente:</strong> {agentToLink?.name}
              </p>
              <p className="text-sm text-blue-700 mt-2">
                Selecione os atendentes que terão este agente IA ativo. Quando um atendente selecionado receber uma mensagem, a IA responderá automaticamente.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-3">Selecione os Atendentes:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {allAgentsUsers.map(agentUser => (
                  <div
                    key={agentUser.id}
                    className={`p-3 border-2 rounded-lg cursor-pointer transition-all ${
                      selectedAgentsUsers.includes(agentUser.id)
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-indigo-300'
                    }`}
                    onClick={() => toggleAgentUser(agentUser.id)}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedAgentsUsers.includes(agentUser.id)}
                        readOnly
                        className="w-4 h-4"
                      />
                      <div>
                        <p className="font-medium">{agentUser.name}</p>
                        <p className="text-xs text-slate-600">{agentUser.email}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {allAgentsUsers.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-4">
                  Nenhum atendente cadastrado. Crie atendentes primeiro.
                </p>
              )}
            </div>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                💡 <strong>Dica:</strong> A IA só funcionará para os atendentes selecionados. 
                Se nenhum atendente for selecionado, o agente ficará desativado.
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowLinkAgentsDialog(false)}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSaveLinkAgents}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700"
              >
                💾 Salvar ({selectedAgentsUsers.length} selecionados)
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    </>
  );
};

// Componente de Configuração do Agente (com abas)
const AgentConfigDialog = ({ agent, open, onClose }) => {
  const [config, setConfig] = useState(agent);

  const handleSave = async () => {
    try {
      await api.put(`/ai/agents/${agent.id}`, config);
      toast.success('Configurações salvas!');
      onClose();
    } catch (error) {
      toast.error('Erro ao salvar configurações');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">⚙️ Configurar: {agent.name}</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="prompt" className="w-full">
          <TabsList className="grid grid-cols-4 mb-4">
            <TabsTrigger value="prompt">Instruções</TabsTrigger>
            <TabsTrigger value="knowledge">Base de Conhecimento</TabsTrigger>
            <TabsTrigger value="model">Tecnologia</TabsTrigger>
            <TabsTrigger value="behavior">Comportamento</TabsTrigger>
          </TabsList>

          {/* Aba: Instruções */}
          <TabsContent value="prompt" className="space-y-4">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-indigo-900 mb-2">📝 Configurações do Prompt</h3>
              <p className="text-sm text-indigo-700">Personalize o prompt do seu Agente</p>
            </div>

            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h4 className="font-semibold text-slate-900 mb-3">Informações Essenciais</h4>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Quem é o seu Agente?</label>
                <Input
                  placeholder="Ex: Sou um assistente especializado em suporte técnico"
                  value={config.who_is || ''}
                  onChange={(e) => setConfig({ ...config, who_is: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">O que seu Agente faz?</label>
                <Input
                  placeholder="Ex: Ajudo clientes com problemas técnicos e dúvidas"
                  value={config.what_does || ''}
                  onChange={(e) => setConfig({ ...config, what_does: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Qual o objetivo do seu Agente?</label>
                <Input
                  placeholder="Ex: Resolver problemas rapidamente e com clareza"
                  value={config.objective || ''}
                  onChange={(e) => setConfig({ ...config, objective: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Como seu Agente deve responder?</label>
                <Textarea
                  placeholder="Ex: De forma clara, objetiva e amigável"
                  value={config.how_respond || ''}
                  onChange={(e) => setConfig({ ...config, how_respond: e.target.value })}
                  rows={3}
                />
              </div>
            </div>

            <div className="bg-white border rounded-lg p-4 space-y-4">
              <h4 className="font-semibold text-slate-900 mb-3">Regras Gerais</h4>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Instruções para o Agente</label>
                <Textarea
                  placeholder="Instruções específicas de como agir"
                  value={config.instructions || ''}
                  onChange={(e) => setConfig({ ...config, instructions: e.target.value })}
                  rows={4}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Quais temas ele deve evitar?</label>
                <Input
                  placeholder="Ex: Política, religião, assuntos pessoais"
                  value={config.avoid_topics || ''}
                  onChange={(e) => setConfig({ ...config, avoid_topics: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Quais palavras ele deve evitar?</label>
                <Input
                  placeholder="Ex: palavrões, termos ofensivos"
                  value={config.avoid_words || ''}
                  onChange={(e) => setConfig({ ...config, avoid_words: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Links permitidos:</label>
                <Textarea
                  placeholder="Cole os links que o agente pode compartilhar (um por linha)"
                  value={config.allowed_links || ''}
                  onChange={(e) => setConfig({ ...config, allowed_links: e.target.value })}
                  rows={3}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Regras personalizadas:</label>
                <Textarea
                  placeholder="Adicione regras customizadas específicas"
                  value={config.custom_rules || ''}
                  onChange={(e) => setConfig({ ...config, custom_rules: e.target.value })}
                  rows={4}
                />
              </div>
            </div>
          </TabsContent>

          {/* Aba: Base de Conhecimento */}
          <TabsContent value="knowledge" className="space-y-4">
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-blue-900 mb-2">📚 Base de Conhecimento</h3>
              <p className="text-sm text-blue-700">Adicione informações que o agente deve conhecer</p>
            </div>

            <Textarea
              placeholder="Cole aqui textos, documentos, FAQs ou qualquer informação que o agente deve usar como referência..."
              value={config.knowledge_base || ''}
              onChange={(e) => setConfig({ ...config, knowledge_base: e.target.value })}
              rows={15}
              className="font-mono text-sm"
            />
          </TabsContent>

          {/* Aba: Tecnologia (Modelo) */}
          <TabsContent value="model" className="space-y-4">
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-purple-900 mb-2">🔧 Configurações do Modelo</h3>
              <p className="text-sm text-purple-700">Configure o modelo de IA que seu Agente vai utilizar</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Provedor LLM</label>
                <select
                  value={config.llm_provider}
                  onChange={(e) => setConfig({ ...config, llm_provider: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="openai">OpenAI</option>
                  <option value="claude">Claude (Anthropic)</option>
                  <option value="gemini">Gemini (Google)</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Modelo</label>
                <select
                  value={config.llm_model}
                  onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="gpt-4o-mini">GPT-4o Mini (Recomendado)</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="gemini-pro">Gemini Pro</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  O modelo GPT-4o oferece respostas mais precisas e segue as instruções com mais eficácia.
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">🔑 API Key</label>
                <Input
                  type="password"
                  placeholder="sk-... ou sua Emergent LLM Key"
                  value={config.api_key || ''}
                  onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Aleatoriedade da resposta (Temperatura): {config.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0 (Consistente)</span>
                  <span>0.5 (Balanceado)</span>
                  <span>1 (Criativo)</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Mantenha em 0.5 para uma resposta mais consistente
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Máximo de Tokens</label>
                <Input
                  type="number"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
                />
              </div>
            </div>
          </TabsContent>

          {/* Aba: Comportamento */}
          <TabsContent value="behavior" className="space-y-4">
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold text-green-900 mb-2">⚙️ Comportamento</h3>
              <p className="text-sm text-green-700">Configure como o agente se comporta</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <input
                  type="checkbox"
                  checked={config.knowledge_restriction}
                  onChange={(e) => setConfig({ ...config, knowledge_restriction: e.target.checked })}
                  className="w-4 h-4"
                />
                <div>
                  <label className="font-medium text-sm">Restrição de conhecimento</label>
                  <p className="text-xs text-slate-500">
                    Quando ativado, algumas instruções extras serão adicionadas ao prompt do sistema
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <input
                  type="checkbox"
                  checked={config.auto_detect_language}
                  onChange={(e) => setConfig({ ...config, auto_detect_language: e.target.checked })}
                  className="w-4 h-4"
                />
                <div>
                  <label className="font-medium text-sm">Detector de Idioma automático</label>
                  <p className="text-xs text-slate-500">
                    Quando ativado, algumas instruções extras são adicionadas ao prompt do sistema
                  </p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Fuso horário</label>
                <select
                  value={config.timezone}
                  onChange={(e) => setConfig({ ...config, timezone: e.target.value })}
                  className="w-full border rounded-lg p-2"
                >
                  <option value="America/Sao_Paulo">America/Sao_Paulo (GMT-3)</option>
                  <option value="America/New_York">America/New_York (GMT-5)</option>
                  <option value="Europe/London">Europe/London (GMT+0)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (GMT+9)</option>
                </select>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Botões de Ação */}
        <div className="flex gap-2 mt-6">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancelar
          </Button>
          <Button onClick={handleSave} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
            💾 Salvar Configurações
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AIAgentsManager;
