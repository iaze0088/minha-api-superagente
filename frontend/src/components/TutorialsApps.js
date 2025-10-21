import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';
import { Trash2, Plus, Save, BookOpen } from 'lucide-react';

const TutorialsApps = () => {
  const [tutorials, setTutorials] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTutorials();
  }, []);

  const loadTutorials = async () => {
    try {
      const { data } = await api.get('/config/tutorials');
      setTutorials(data || []);
    } catch (error) {
      console.error('Erro ao carregar tutoriais:', error);
    }
  };

  const addNewTutorial = () => {
    setTutorials([
      ...tutorials,
      {
        id: Date.now().toString(),
        category: '',
        appName: '',
        code: '',
        instructions: '',
        videoUrl: '',
        active: true
      }
    ]);
  };

  const updateTutorial = (id, field, value) => {
    setTutorials(tutorials.map(tut => 
      tut.id === id ? { ...tut, [field]: value } : tut
    ));
  };

  const deleteTutorial = (id) => {
    setTutorials(tutorials.filter(tut => tut.id !== id));
  };

  const saveTutorials = async () => {
    try {
      setLoading(true);
      await api.post('/config/tutorials', { tutorials });
      toast.success('Tutoriais salvos com sucesso!');
    } catch (error) {
      toast.error('Erro ao salvar tutoriais');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>📚 Tutoriais / Aplicativos</span>
          <Button onClick={addNewTutorial} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Novo Tutorial
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {tutorials.length === 0 ? (
            <p className="text-center text-slate-500 py-8">
              Nenhum tutorial configurado. Clique em "Novo Tutorial" para começar.
            </p>
          ) : (
            tutorials.map((tut) => (
              <div key={tut.id} className="border rounded-lg p-4 space-y-3 bg-gradient-to-r from-purple-50 to-blue-50">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-lg flex items-center gap-2">
                    <BookOpen className="w-5 h-5" />
                    Bloco de Tutorial
                  </label>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => deleteTutorial(tut.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-medium text-sm block mb-1">Categoria/Dispositivo:</label>
                    <Input
                      placeholder="Ex: Smart TV, TV Box, Celular Android..."
                      value={tut.category}
                      onChange={(e) => updateTutorial(tut.id, 'category', e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <label className="font-medium text-sm block mb-1">Nome do Aplicativo:</label>
                    <Input
                      placeholder="Ex: XCLOUD, ASSIST PLUS, LAZER PLAY..."
                      value={tut.appName}
                      onChange={(e) => updateTutorial(tut.id, 'appName', e.target.value)}
                    />
                  </div>
                </div>
                
                <div>
                  <label className="font-medium text-sm block mb-1">Código/Provedor:</label>
                  <Input
                    placeholder="Ex: rota01, norte, 81618..."
                    value={tut.code}
                    onChange={(e) => updateTutorial(tut.id, 'code', e.target.value)}
                  />
                </div>
                
                <div>
                  <label className="font-medium text-sm block mb-1">Instruções de Configuração:</label>
                  <Textarea
                    placeholder="Ex: 1. Baixe o app XCLOUD&#10;2. Configure provedor: rota01&#10;3. Faça login com usuário e senha..."
                    value={tut.instructions}
                    onChange={(e) => updateTutorial(tut.id, 'instructions', e.target.value)}
                    rows={4}
                  />
                </div>
                
                <div>
                  <label className="font-medium text-sm block mb-1">Link do Vídeo Tutorial (opcional):</label>
                  <Input
                    placeholder="https://youtube.com/..."
                    value={tut.videoUrl}
                    onChange={(e) => updateTutorial(tut.id, 'videoUrl', e.target.value)}
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={tut.active}
                    onChange={(e) => updateTutorial(tut.id, 'active', e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label className="text-sm">Ativo (visível para atendentes)</label>
                </div>
              </div>
            ))
          )}
          
          <Button 
            onClick={saveTutorials} 
            disabled={loading}
            className="w-full"
          >
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Salvando...' : 'Salvar Todos os Tutoriais'}
          </Button>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
            <p className="font-medium mb-2">💡 Como os Atendentes Verão:</p>
            <ul className="list-disc list-inside space-y-1 text-slate-700">
              <li>Lista organizada por categoria (Smart TV, TV Box, etc)</li>
              <li>Botão de "Enviar ao Cliente" para cada tutorial</li>
              <li>Copiar instruções com 1 clique</li>
              <li>Acessível no painel lateral do atendente</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TutorialsApps;
