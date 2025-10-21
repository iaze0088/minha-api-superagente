import { useState, useEffect } from 'react';
import { Plus, Trash2, Upload, Clock, MessageSquare, Image, Video, Music, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import api from '../lib/api';

const AutoResponderAdvanced = () => {
  const [sequences, setSequences] = useState([]);
  const [showEditor, setShowEditor] = useState(false);
  const [currentSequence, setCurrentSequence] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSequences();
  }, []);

  const loadSequences = async () => {
    try {
      const { data } = await api.get('/config/auto-responder-sequences');
      setSequences(data);
    } catch (error) {
      console.error('Erro ao carregar sequências:', error);
      toast.error('Erro ao carregar auto-responder');
    }
  };

  const createNewSequence = () => {
    setCurrentSequence({
      id: Date.now().toString() + Math.random().toString(36),
      trigger: '',
      responses: [],
      enabled: true
    });
    setShowEditor(true);
  };

  const editSequence = (sequence) => {
    setCurrentSequence({...sequence});
    setShowEditor(true);
  };

  const addResponse = () => {
    if (!currentSequence) return;
    
    const newResponse = {
      id: Date.now().toString() + Math.random().toString(36),
      type: 'text',
      content: '',
      delay: 0
    };
    
    setCurrentSequence({
      ...currentSequence,
      responses: [...currentSequence.responses, newResponse]
    });
  };

  const updateResponse = (responseId, field, value) => {
    setCurrentSequence({
      ...currentSequence,
      responses: currentSequence.responses.map(r =>
        r.id === responseId ? { ...r, [field]: value } : r
      )
    });
  };

  const removeResponse = (responseId) => {
    setCurrentSequence({
      ...currentSequence,
      responses: currentSequence.responses.filter(r => r.id !== responseId)
    });
  };

  const handleFileUpload = async (responseId, file) => {
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
      
      updateResponse(responseId, 'content', data.url);
      updateResponse(responseId, 'type', type);
      
      toast.success('Arquivo enviado com sucesso!');
    } catch (error) {
      console.error('Erro no upload:', error);
      toast.error('Erro ao fazer upload do arquivo');
    } finally {
      setUploading(false);
    }
  };

  const saveSequence = async () => {
    if (!currentSequence.trigger.trim()) {
      toast.error('Digite uma palavra-chave para acionar a sequência');
      return;
    }
    
    if (currentSequence.responses.length === 0) {
      toast.error('Adicione pelo menos uma resposta');
      return;
    }
    
    // Validar que todas as respostas têm conteúdo
    const emptyResponses = currentSequence.responses.filter(r => !r.content.trim());
    if (emptyResponses.length > 0) {
      toast.error('Todas as respostas devem ter conteúdo');
      return;
    }
    
    setLoading(true);
    try {
      // Atualizar ou adicionar sequência
      const updatedSequences = sequences.some(s => s.id === currentSequence.id)
        ? sequences.map(s => s.id === currentSequence.id ? currentSequence : s)
        : [...sequences, currentSequence];
      
      await api.post('/config/auto-responder-sequences', {
        sequences: updatedSequences
      });
      
      setSequences(updatedSequences);
      setShowEditor(false);
      setCurrentSequence(null);
      toast.success('Sequência salva com sucesso!');
    } catch (error) {
      console.error('Erro ao salvar:', error);
      toast.error('Erro ao salvar sequência');
    } finally {
      setLoading(false);
    }
  };

  const deleteSequence = async (sequenceId) => {
    if (!confirm('Tem certeza que deseja excluir esta sequência?')) return;
    
    try {
      const updatedSequences = sequences.filter(s => s.id !== sequenceId);
      await api.post('/config/auto-responder-sequences', {
        sequences: updatedSequences
      });
      setSequences(updatedSequences);
      toast.success('Sequência excluída!');
    } catch (error) {
      console.error('Erro ao excluir:', error);
      toast.error('Erro ao excluir sequência');
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

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Auto-Responder Avançado</h2>
        <Button onClick={createNewSequence} className="flex items-center gap-2">
          <Plus className="w-4 h-4" /> Nova Sequência
        </Button>
      </div>

      {/* Lista de Sequências */}
      <div className="grid gap-4">
        {sequences.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-gray-500">
              Nenhuma sequência criada ainda. Clique em "Nova Sequência" para começar.
            </CardContent>
          </Card>
        ) : (
          sequences.map(sequence => (
            <Card key={sequence.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">
                      Trigger: "{sequence.trigger}"
                    </CardTitle>
                    <p className="text-sm text-gray-500 mt-1">
                      {sequence.responses.length} resposta(s) • {sequence.enabled ? '✅ Ativa' : '❌ Inativa'}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => editSequence(sequence)}>
                      Editar
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteSequence(sequence.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {sequence.responses.map((response, idx) => (
                    <div key={response.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <span className="font-bold text-sm">{idx + 1}.</span>
                      {getTypeIcon(response.type)}
                      <span className="text-sm flex-1 truncate">
                        {response.type === 'text' ? response.content : `[${response.type}]`}
                      </span>
                      {response.delay > 0 && (
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {response.delay}s
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Editor de Sequência */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {currentSequence?.id && sequences.some(s => s.id === currentSequence.id)
                ? 'Editar Sequência'
                : 'Nova Sequência'}
            </DialogTitle>
          </DialogHeader>

          {currentSequence && (
            <div className="space-y-4">
              {/* Trigger */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Palavra-Chave (Trigger)
                </label>
                <Input
                  value={currentSequence.trigger}
                  onChange={(e) => setCurrentSequence({...currentSequence, trigger: e.target.value})}
                  placeholder="Ex: ajuda, info, tutorial"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Quando o cliente digitar esta palavra, a sequência será acionada
                </p>
              </div>

              {/* Status */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={currentSequence.enabled}
                  onChange={(e) => setCurrentSequence({...currentSequence, enabled: e.target.checked})}
                  className="w-4 h-4"
                />
                <label className="text-sm">Sequência ativa</label>
              </div>

              {/* Respostas */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium">Respostas Sequenciais</label>
                  <Button size="sm" onClick={addResponse} className="flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Adicionar Resposta
                  </Button>
                </div>

                <div className="space-y-4">
                  {currentSequence.responses.map((response, idx) => (
                    <Card key={response.id}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-bold">Resposta {idx + 1}</h4>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeResponse(response.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>

                        {/* Tipo */}
                        <div className="mb-3">
                          <label className="block text-sm font-medium mb-1">Tipo</label>
                          <select
                            value={response.type}
                            onChange={(e) => {
                              updateResponse(response.id, 'type', e.target.value);
                              if (e.target.value !== 'text') {
                                updateResponse(response.id, 'content', '');
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
                          {response.type === 'text' ? (
                            <Textarea
                              value={response.content}
                              onChange={(e) => updateResponse(response.id, 'content', e.target.value)}
                              placeholder="Digite a mensagem..."
                              rows={3}
                            />
                          ) : (
                            <div className="space-y-2">
                              {response.content && (
                                <div className="p-2 bg-green-50 border border-green-200 rounded text-sm">
                                  ✅ Arquivo carregado: {response.content.split('/').pop()}
                                </div>
                              )}
                              <div className="flex items-center gap-2">
                                <input
                                  type="file"
                                  id={`file-${response.id}`}
                                  accept={
                                    response.type === 'photo' ? 'image/*' :
                                    response.type === 'video' ? 'video/*' :
                                    response.type === 'audio' ? 'audio/*' : '*'
                                  }
                                  onChange={(e) => handleFileUpload(response.id, e.target.files[0])}
                                  className="hidden"
                                  disabled={uploading}
                                />
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={() => document.getElementById(`file-${response.id}`).click()}
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
                              value={response.delay}
                              onChange={(e) => updateResponse(response.id, 'delay', parseInt(e.target.value))}
                              className="flex-1"
                            />
                            <span className="w-12 text-center font-bold">{response.delay}s</span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Tempo de espera antes de enviar esta resposta
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
                <Button onClick={saveSequence} disabled={loading} className="flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  {loading ? 'Salvando...' : 'Salvar Sequência'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AutoResponderAdvanced;
