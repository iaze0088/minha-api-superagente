import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import api from '@/lib/api';
import { toast } from 'sonner';

const DepartmentsManager = () => {
  const [departments, setDepartments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    ai_agent_id: '',
    is_default: false,
    timeout_seconds: 120
  });

  useEffect(() => {
    loadDepartments();
    loadAgents();
  }, []);

  const loadDepartments = async () => {
    try {
      const { data } = await api.get('/ai/departments');
      setDepartments(data);
    } catch (error) {
      console.error('Error loading departments:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const { data } = await api.get('/ai/agents');
      setAgents(data.filter(a => a.is_active));
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('Digite um nome para o departamento');
      return;
    }

    try {
      if (editingDept) {
        await api.put(`/ai/departments/${editingDept.id}`, formData);
        toast.success('Departamento atualizado!');
      } else {
        await api.post('/ai/departments', formData);
        toast.success('Departamento criado!');
      }
      
      setShowDialog(false);
      setEditingDept(null);
      setFormData({
        name: '',
        description: '',
        ai_agent_id: '',
        is_default: false,
        timeout_seconds: 120
      });
      loadDepartments();
    } catch (error) {
      toast.error('Erro ao salvar departamento');
    }
  };

  const handleEdit = (dept) => {
    setEditingDept(dept);
    setFormData({
      name: dept.name,
      description: dept.description || '',
      ai_agent_id: dept.ai_agent_id || '',
      is_default: dept.is_default,
      timeout_seconds: dept.timeout_seconds
    });
    setShowDialog(true);
  };

  const handleDelete = async (deptId) => {
    if (!confirm('Tem certeza que deseja deletar este departamento?')) return;

    try {
      await api.delete(`/ai/departments/${deptId}`);
      toast.success('Departamento deletado!');
      loadDepartments();
    } catch (error) {
      toast.error('Erro ao deletar departamento');
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">📂 Departamentos</h2>
        <p className="text-slate-600 mb-4">Gerencie os departamentos de atendimento</p>
        
        <Button 
          onClick={() => {
            setEditingDept(null);
            setFormData({
              name: '',
              description: '',
              ai_agent_id: '',
              is_default: false,
              timeout_seconds: 120
            });
            setShowDialog(true);
          }}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Departamento
        </Button>
      </div>

      {/* Lista de Departamentos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {departments.map(dept => {
          const linkedAgent = agents.find(a => a.id === dept.ai_agent_id);
          
          return (
            <Card key={dept.id} className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-slate-900">{dept.name}</h3>
                  {dept.is_default && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded mt-1 inline-block">
                      Padrão
                    </span>
                  )}
                </div>
                
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleEdit(dept)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(dept.id)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
              
              <p className="text-sm text-slate-600 mb-3">{dept.description || 'Sem descrição'}</p>
              
              <div className="space-y-2 text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  <span>Timeout: {dept.timeout_seconds}s</span>
                </div>
                {linkedAgent && (
                  <div className="flex items-center gap-2 text-indigo-600">
                    <span>🤖</span>
                    <span>{linkedAgent.name}</span>
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Dialog: Criar/Editar Departamento */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingDept ? 'Editar' : 'Criar'} Departamento</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Nome</label>
              <Input
                placeholder="Ex: Suporte, Vendas, Teste Grátis"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Descrição</label>
              <Textarea
                placeholder="Descreva este departamento"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Agente IA vinculado</label>
              <select
                value={formData.ai_agent_id}
                onChange={(e) => setFormData({ ...formData, ai_agent_id: e.target.value })}
                className="w-full border rounded-lg p-2"
              >
                <option value="">Nenhum</option>
                {agents.map(agent => (
                  <option key={agent.id} value={agent.id}>{agent.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Timeout (segundos)</label>
              <Input
                type="number"
                placeholder="120"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
              />
              <p className="text-xs text-slate-500 mt-1">
                Tempo para redirecionar automaticamente para este departamento se o cliente não responder
              </p>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_default}
                onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                className="w-4 h-4"
              />
              <label className="text-sm">
                Marcar como departamento padrão (recebe tickets após timeout)
              </label>
            </div>

            <div className="flex gap-2 mt-4">
              <Button variant="outline" onClick={() => setShowDialog(false)} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleSave} className="flex-1 bg-indigo-600 hover:bg-indigo-700">
                {editingDept ? 'Atualizar' : 'Criar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DepartmentsManager;
