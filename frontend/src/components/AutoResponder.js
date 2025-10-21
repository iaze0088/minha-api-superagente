import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';
import { Trash2, Plus, Save } from 'lucide-react';

const AutoResponder = () => {
  const [autoResponses, setAutoResponses] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAutoResponses();
  }, []);

  const loadAutoResponses = async () => {
    try {
      const { data } = await api.get('/config/auto-responses');
      setAutoResponses(data || []);
    } catch (error) {
      console.error('Erro ao carregar auto-respostas:', error);
    }
  };

  const addNewResponse = () => {
    setAutoResponses([
      ...autoResponses,
      {
        id: Date.now().toString(),
        trigger: '',
        response: '',
        active: true
      }
    ]);
  };

  const updateResponse = (id, field, value) => {
    setAutoResponses(autoResponses.map(resp => 
      resp.id === id ? { ...resp, [field]: value } : resp
    ));
  };

  const deleteResponse = (id) => {
    setAutoResponses(autoResponses.filter(resp => resp.id !== id));
  };

  const saveAutoResponses = async () => {
    try {
      setLoading(true);
      await api.post('/config/auto-responses', { responses: autoResponses });
      toast.success('Auto-respostas salvas com sucesso!');
    } catch (error) {
      toast.error('Erro ao salvar auto-respostas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>⚡ Auto-Responder (FAQ Automático)</span>
          <Button onClick={addNewResponse} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Nova Resposta
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {autoResponses.length === 0 ? (
            <p className="text-center text-slate-500 py-8">
              Nenhuma auto-resposta configurada. Clique em "Nova Resposta" para começar.
            </p>
          ) : (
            autoResponses.map((resp) => (
              <div key={resp.id} className="border rounded-lg p-4 space-y-3 bg-slate-50">
                <div className="flex items-center justify-between">
                  <label className="font-medium text-sm">Pergunta/Gatilho:</label>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => deleteResponse(resp.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <Input
                  placeholder="Ex: qual o valor, quanto custa, preço..."
                  value={resp.trigger}
                  onChange={(e) => updateResponse(resp.id, 'trigger', e.target.value)}
                />
                
                <label className="font-medium text-sm block">Resposta Automática:</label>
                <Textarea
                  placeholder="Ex: Nossos planos custam R$ 15/mês com 3 telas simultâneas..."
                  value={resp.response}
                  onChange={(e) => updateResponse(resp.id, 'response', e.target.value)}
                  rows={3}
                />
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={resp.active}
                    onChange={(e) => updateResponse(resp.id, 'active', e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label className="text-sm">Ativo</label>
                </div>
              </div>
            ))
          )}
          
          <Button 
            onClick={saveAutoResponses} 
            disabled={loading}
            className="w-full"
          >
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Salvando...' : 'Salvar Todas as Auto-Respostas'}
          </Button>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
            <p className="font-medium mb-2">💡 Como Funciona:</p>
            <ul className="list-disc list-inside space-y-1 text-slate-700">
              <li>Quando cliente enviar mensagem com o gatilho, resposta automática é enviada ANTES da IA</li>
              <li>Use palavras-chave simples (ex: "valor", "preço", "teste")</li>
              <li>Sistema busca correspondência parcial (não precisa ser exato)</li>
              <li>Após resposta automática, IA também pode responder normalmente</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AutoResponder;
