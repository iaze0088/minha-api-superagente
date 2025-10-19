import { useState } from 'react';
import { GitBranch, Settings, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { TabsContent } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '../lib/api';
import ResellerList from './ResellerList';
import ResellerTree from './ResellerTree';

const ResellerManagement = ({ resellers, hierarchy, loadData, handleReplicateConfig }) => {
  const [newReseller, setNewReseller] = useState({ name: '', email: '', password: '', domain: '', parent_id: null });
  const [expandedResellers, setExpandedResellers] = useState(new Set());
  const [transferModal, setTransferModal] = useState({ open: false, reseller: null, new_parent_id: null });
  const [viewMode, setViewMode] = useState('list');

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
      setTransferModal({ open: false, reseller: null, new_parent_id: null });
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

  return (
    <>
      <TabsContent value="resellers" className="space-y-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold">Gerenciar Revendas Multi-Tenant</h3>
              <p className="text-sm text-slate-600 mt-1">Hierarquia completa com isolamento de dados</p>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={() => setViewMode(viewMode === 'list' ? 'tree' : 'list')} 
                variant="outline"
                size="sm"
              >
                <GitBranch className="w-4 h-4 mr-2" />
                {viewMode === 'list' ? 'Ver Hierarquia' : 'Ver Lista'}
              </Button>
              <Button onClick={handleReplicateConfig} variant="outline" size="sm" className="bg-blue-600 text-white hover:bg-blue-700">
                <Settings className="w-4 h-4 mr-2" />
                Replicar Config
              </Button>
            </div>
          </div>
          
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-purple-900">
              <strong>🌳 Sistema Multi-Tenant Hierárquico</strong><br />
              • Cada revenda tem domínio próprio e dados isolados<br />
              • Revendas podem criar sub-revendas (hierarquia ilimitada)<br />
              • Transferência de revendas entre pais (Admin Master only)<br />
              • Exclusão bloqueada se houver sub-revendas
            </p>
          </div>
          
          <h4 className="font-semibold mb-3">Criar Nova Revenda</h4>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <Input
              placeholder="Nome da Revenda"
              value={newReseller.name}
              onChange={(e) => setNewReseller({ ...newReseller, name: e.target.value })}
            />
            <Input
              placeholder="Email (login)"
              type="email"
              value={newReseller.email}
              onChange={(e) => setNewReseller({ ...newReseller, email: e.target.value })}
            />
            <Input
              type="password"
              placeholder="Senha"
              value={newReseller.password}
              onChange={(e) => setNewReseller({ ...newReseller, password: e.target.value })}
            />
          </div>
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <Input
              placeholder="Domínio (opcional)"
              value={newReseller.domain}
              onChange={(e) => setNewReseller({ ...newReseller, domain: e.target.value })}
            />
            <Select value={newReseller.parent_id || 'root'} onValueChange={(val) => setNewReseller({ ...newReseller, parent_id: val === 'root' ? null : val })}>
              <SelectTrigger>
                <SelectValue placeholder="Revenda Pai (Raiz se vazio)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="root">🌟 Revenda Raiz (Nível 0)</SelectItem>
                {resellers.map(r => (
                  <SelectItem key={r.id} value={r.id}>
                    {'  '.repeat(r.level || 0)}└─ {r.name} (Nível {r.level || 0})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleCreateReseller} className="bg-purple-600 hover:bg-purple-700">
            <Plus className="w-4 h-4 mr-2" />
            Criar Revenda
          </Button>
        </Card>

        {viewMode === 'list' ? (
          <ResellerList 
            resellers={resellers}
            loadData={loadData}
            handleDeleteReseller={handleDeleteReseller}
            setTransferModal={setTransferModal}
          />
        ) : (
          <ResellerTree
            hierarchy={hierarchy}
            expandedResellers={expandedResellers}
            toggleExpand={toggleExpand}
            handleDeleteReseller={handleDeleteReseller}
            setTransferModal={setTransferModal}
          />
        )}
      </TabsContent>

      <Dialog open={transferModal.open} onOpenChange={(open) => setTransferModal({ ...transferModal, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Transferir Revenda</DialogTitle>
          </DialogHeader>
          {transferModal.reseller && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded">
                <p className="text-sm text-slate-600">Revenda:</p>
                <p className="font-semibold">{transferModal.reseller.name}</p>
                <p className="text-xs text-slate-500">Nível atual: {transferModal.reseller.level || 0}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Nova Revenda Pai:</label>
                <Select 
                  value={transferModal.new_parent_id || 'root'} 
                  onValueChange={(val) => setTransferModal({ ...transferModal, new_parent_id: val === 'root' ? null : val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecionar nova pai" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="root">🌟 Tornar Raiz (Nível 0)</SelectItem>
                    {resellers
                      .filter(r => r.id !== transferModal.reseller.id)
                      .map(r => (
                        <SelectItem key={r.id} value={r.id}>
                          {'  '.repeat(r.level || 0)}└─ {r.name} (Nível {r.level || 0})
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setTransferModal({ open: false, reseller: null, new_parent_id: null })}>
                  Cancelar
                </Button>
                <Button onClick={handleTransferReseller} className="bg-purple-600 hover:bg-purple-700">
                  Transferir
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ResellerManagement;

