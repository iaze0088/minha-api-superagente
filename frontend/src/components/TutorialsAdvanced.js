import { useState, useEffect } from 'react';
import { Plus, Trash2, Upload, Clock, MessageSquare, Image, Video, Music, Save, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import api from '../lib/api';

const TutorialsAdvanced = () => {
  const [tutorials, setTutorials] = useState([]);
  const [showEditor, setShowEditor] = useState(false);
  const [currentTutorial, setCurrentTutorial] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTutorials();
  }, []);

  const loadTutorials = async () => {
    try {
      const { data } = await api.get('/config/tutorials-advanced');
      setTutorials(data);
    } catch (error) {
      console.error('Erro ao carregar tutoriais:', error);
      toast.error('Erro ao carregar tutoriais');
    }
  };

  const createNewTutorial = () => {
    setCurrentTutorial({
      id: Date.now().toString() + Math.random().toString(36),
      category: '',
      title: '',
      items: [],
      enabled: true
    });
    setShowEditor(true);
  };

  const editTutorial = (tutorial) => {
    setCurrentTutorial({...tutorial});
    setShowEditor(true);
  };

  const addItem = () => {
    if (!currentTutorial) return;
    
    const newItem = {
      id: Date.now().toString() + Math.random().toString(36),
      type: 'text',
      content: '',
      delay: 0
    };
    
    setCurrentTutorial({
      ...currentTutorial,
      items: [...currentTutorial.items, newItem]
    });
  };

  const updateItem = (itemId, field, value) => {
    setCurrentTutorial({
      ...currentTutorial,
      items: currentTutorial.items.map(item =>
        item.id === itemId ? { ...item, [field]: value } : item
      )
    });
  };

  const removeItem = (itemId) => {
    setCurrentTutorial({
      ...currentTutorial,
      items: currentTutorial.items.filter(item => item.id !== itemId)
    });
  };

  const handleFileUpload = async (itemId, file) => {
    if (!file) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const { data } = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      // Determinar tipo baseado no mime
      let type = 'file';
      if (data.kind === 'image') type = 'photo';
      else if (data.kind === 'video') type = 'video';
      else if (data.kind === 'audio') type = 'audio';
      
      updateItem(itemId, 'content', data.url);
      updateItem(itemId, 'type', type);
      
      toast.success('Arquivo enviado com sucesso!');
    } catch (error) {
      console.error('Erro no upload:', error);
      toast.error('Erro ao fazer upload do arquivo');
    } finally {
      setUploading(false);
    }
  };

  const saveTutorial = async () => {
    if (!currentTutorial.title.trim()) {
      toast.error('Digite um título para o tutorial');
      return;
    }
    
    if (!currentTutorial.category.trim()) {
      toast.error('Digite uma categoria');
      return;
    }
    
    if (currentTutorial.items.length === 0) {
      toast.error('Adicione pelo menos um item ao tutorial');
      return;
    }
    
    // Validar que todos os itens têm conteúdo
    const emptyItems = currentTutorial.items.filter(item => !item.content.trim());
    if (emptyItems.length > 0) {
      toast.error('Todos os itens devem ter conteúdo');
      return;
    }
    
    setLoading(true);
    try {
      // Atualizar ou adicionar tutorial
      const updatedTutorials = tutorials.some(t => t.id === currentTutorial.id)
        ? tutorials.map(t => t.id === currentTutorial.id ? currentTutorial : t)
        : [...tutorials, currentTutorial];
      
      await api.post('/config/tutorials-advanced', {
        tutorials: updatedTutorials
      });
      
      setTutorials(updatedTutorials);
      setShowEditor(false);
      setCurrentTutorial(null);
      toast.success('Tutorial salvo com sucesso!');
    } catch (error) {
      console.error('Erro ao salvar:', error);
      toast.error('Erro ao salvar tutorial');
    } finally {
      setLoading(false);
    }
  };

  const deleteTutorial = async (tutorialId) => {
    if (!confirm('Tem certeza que deseja excluir este tutorial?')) return;
    
    try {
      const updatedTutorials = tutorials.filter(t => t.id !== tutorialId);
      await api.post('/config/tutorials-advanced', {
        tutorials: updatedTutorials
      });
      setTutorials(updatedTutorials);
      toast.success('Tutorial excluído!');
    } catch (error) {
      console.error('Erro ao excluir:', error);
      toast.error('Erro ao excluir tutorial');
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'text': return <MessageSquare className="w-4 h-4" />;
      case 'photo': return <Image className="w-4 h-4" />;
      case 'video': return <Video className="w-4 h-4" />;
      case 'audio': return <Music className="w-4 h-4" />;
      default: return <MessageSquare className="w-4 h-4" />;
    }
  };

  const groupedTutorials = tutorials.reduce((acc, tutorial) => {
    if (!acc[tutorial.category]) {
      acc[tutorial.category] = [];
    }
    acc[tutorial.category].push(tutorial);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Tutoriais & Aplicativos</h2>
        <Button onClick={createNewTutorial} className="flex items-center gap-2">
          <Plus className="w-4 h-4" /> Novo Tutorial
        </Button>
      </div>

      {/* Lista de Tutoriais Agrupados por Categoria */}
      <div className="space-y-6">
        {Object.keys(groupedTutorials).length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-gray-500">
              Nenhum tutorial criado ainda. Clique em "Novo Tutorial" para começar.
            </CardContent>
          </Card>
        ) : (
          Object.entries(groupedTutorials).map(([category, categoryTutorials]) => (
            <div key={category}>
              <div className="flex items-center gap-2 mb-3">
                <FolderOpen className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-bold text-blue-600">{category}</h3>
                <span className="text-sm text-gray-500">({categoryTutorials.length})</span>
              </div>
              
              <div className="grid gap-4">
                {categoryTutorials.map(tutorial => (
                  <Card key={tutorial.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">{tutorial.title}</CardTitle>
                          <p className="text-sm text-gray-500 mt-1">
                            {tutorial.items.length} item(ns) • {tutorial.enabled ? '✅ Ativo' : '❌ Inativo'}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => editTutorial(tutorial)}>
                            Editar
                          </Button>
                          <Button variant="destructive" size="sm" onClick={() => deleteTutorial(tutorial.id)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {tutorial.items.slice(0, 3).map((item, idx) => (
                          <div key={item.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                            <span className="font-bold text-sm">{idx + 1}.</span>
                            {getTypeIcon(item.type)}
                            <span className="text-sm flex-1 truncate">
                              {item.type === 'text' ? item.content : `[${item.type}]`}
                            </span>
                            {item.delay > 0 && (
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" /> {item.delay}s
                              </span>
                            )}
                          </div>
                        ))}
                        {tutorial.items.length > 3 && (
                          <p className="text-xs text-gray-500 text-center">
                            ... e mais {tutorial.items.length - 3} item(ns)
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Editor de Tutorial */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {currentTutorial?.id && tutorials.some(t => t.id === currentTutorial.id)
                ? 'Editar Tutorial'
                : 'Novo Tutorial'}
            </DialogTitle>
          </DialogHeader>

          {currentTutorial && (
            <div className="space-y-4">
              {/* Informações Básicas */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Categoria</label>
                  <Input
                    value={currentTutorial.category}
                    onChange={(e) => setCurrentTutorial({...currentTutorial, category: e.target.value})}
                    placeholder="Ex: Setup, FAQ, Como Usar"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Título</label>
                  <Input
                    value={currentTutorial.title}
                    onChange={(e) => setCurrentTutorial({...currentTutorial, title: e.target.value})}
                    placeholder="Ex: Como fazer login"
                  />
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={currentTutorial.enabled}
                  onChange={(e) => setCurrentTutorial({...currentTutorial, enabled: e.target.checked})}
                  className="w-4 h-4"
                />
                <label className="text-sm">Tutorial ativo</label>
              </div>

              {/* Itens do Tutorial */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium">Itens do Tutorial</label>
                  <Button size="sm" onClick={addItem} className="flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Adicionar Item
                  </Button>
                </div>

                <div className="space-y-4">
                  {currentTutorial.items.map((item, idx) => (
                    <Card key={item.id}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-bold">Item {idx + 1}</h4>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeItem(item.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>

                        {/* Tipo */}
                        <div className="mb-3">
                          <label className="block text-sm font-medium mb-1">Tipo</label>
                          <select
                            value={item.type}
                            onChange={(e) => {
                              updateItem(item.id, 'type', e.target.value);
                              if (e.target.value !== 'text') {
                                updateItem(item.id, 'content', '');
                              }
                            }}
                            className="w-full p-2 border rounded"
                          >
                            <option value="text">Texto</option>
                            <option value="photo">Foto</option>
                            <option value="video">Vídeo</option>
                            <option value="audio">Áudio</option>
                          </select>
                        </div>

                        {/* Conteúdo */}
                        <div className="mb-3">
                          <label className="block text-sm font-medium mb-1">Conteúdo</label>
                          {item.type === 'text' ? (
                            <Textarea
                              value={item.content}
                              onChange={(e) => updateItem(item.id, 'content', e.target.value)}
                              placeholder="Digite o conteúdo..."
                              rows={3}
                            />
                          ) : (
                            <div className="space-y-2">
                              {item.content && (
                                <div className="p-2 bg-green-50 border border-green-200 rounded text-sm">
                                  ✅ Arquivo carregado: {item.content.split('/').pop()}
                                </div>
                              )}
                              <div className="flex items-center gap-2">
                                <input
                                  type="file"
                                  id={`file-${item.id}`}
                                  accept={
                                    item.type === 'photo' ? 'image/*' :
                                    item.type === 'video' ? 'video/*' :
                                    item.type === 'audio' ? 'audio/*' : '*'
                                  }
                                  onChange={(e) => handleFileUpload(item.id, e.target.files[0])}
                                  className="hidden"
                                  disabled={uploading}
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={() => document.getElementById(`file-${item.id}`).click()}
                                  disabled={uploading}
                                  className="flex items-center gap-2"
                                >
                                  <Upload className="w-4 h-4" />
                                  {uploading ? 'Enviando...' : 'Upload Arquivo'}
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Delay */}
                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Delay (segundos)
                          </label>
                          <div className="flex items-center gap-2">
                            <input
                              type="range"
                              min="0"
                              max="60"
                              value={item.delay}
                              onChange={(e) => updateItem(item.id, 'delay', parseInt(e.target.value))}
                              className="flex-1"
                            />
                            <span className="w-12 text-center font-bold">{item.delay}s</span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Tempo de espera antes de enviar este item
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Botões de Ação */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setShowEditor(false)}>
                  Cancelar
                </Button>
                <Button onClick={saveTutorial} disabled={loading} className="flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  {loading ? 'Salvando...' : 'Salvar Tutorial'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TutorialsAdvanced;
