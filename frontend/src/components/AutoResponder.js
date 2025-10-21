import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';
import { Trash2, Plus, Save, Image, Video, Mic, Type, Clock } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

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
        messages: [
          {
            id: Date.now().toString() + '-1',
            type: 'text',
            content: '',
            delay: 0
          }
        ],
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

  const addMessage = (responseId) => {
    setAutoResponses(autoResponses.map(resp => {
      if (resp.id === responseId) {
        return {
          ...resp,
          messages: [
            ...resp.messages,
            {
              id: Date.now().toString(),
              type: 'text',
              content: '',
              delay: 3
            }
          ]
        };
      }
      return resp;
    }));
  };

  const updateMessage = (responseId, messageId, field, value) => {
    setAutoResponses(autoResponses.map(resp => {
      if (resp.id === responseId) {
        return {
          ...resp,
          messages: resp.messages.map(msg =>
            msg.id === messageId ? { ...msg, [field]: value } : msg
          )
        };
      }
      return resp;
    }));
  };

  const deleteMessage = (responseId, messageId) => {
    setAutoResponses(autoResponses.map(resp => {
      if (resp.id === responseId) {
        return {
          ...resp,
          messages: resp.messages.filter(msg => msg.id !== messageId)
        };
      }
      return resp;
    }));
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

  const getMessageIcon = (type) => {
    switch(type) {
      case 'text': return <Type className="w-4 h-4" />;
      case 'image': return <Image className="w-4 h-4" />;
      case 'video': return <Video className="w-4 h-4" />;
      case 'audio': return <Mic className="w-4 h-4" />;
      default: return <Type className="w-4 h-4" />;
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
        <div className="space-y-6">
          {autoResponses.length === 0 ? (
            <p className="text-center text-slate-500 py-8">
              Nenhuma auto-resposta configurada. Clique em "Nova Resposta" para começar.
            </p>
          ) : (
            autoResponses.map((resp) => (
              <div key={resp.id} className="border-2 border-indigo-200 rounded-lg p-4 space-y-4 bg-gradient-to-r from-indigo-50 to-purple-50">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <label className="font-bold text-lg">🎯 Gatilho de Resposta</label>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => deleteResponse(resp.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* Gatilho/Pergunta */}
                <div>
                  <label className="font-medium text-sm block mb-1">Pergunta/Gatilho:</label>
                  <Input
                    placeholder="Ex: qual o valor, quanto custa, preço, teste gratis..."
                    value={resp.trigger}
                    onChange={(e) => updateResponse(resp.id, 'trigger', e.target.value)}
                  />
                  <p className="text-xs text-slate-500 mt-1">Use palavras-chave separadas por vírgula</p>
                </div>
                
                {/* Mensagens da Resposta */}
                <div className="space-y-3 border-t-2 border-indigo-200 pt-4">
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-md">📨 Sequência de Respostas:</label>
                    <Button
                      size="sm"
                      onClick={() => addMessage(resp.id)}
                      variant="outline"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Adicionar Mensagem
                    </Button>
                  </div>
                  
                  {resp.messages.map((msg, idx) => (
                    <div key={msg.id} className="border border-slate-300 rounded-lg p-3 bg-white space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm">Mensagem #{idx + 1}</span>
                        {resp.messages.length > 1 && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteMessage(resp.id, msg.id)}
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </Button>
                        )}
                      </div>
                      
                      {/* Tipo de Mensagem */}
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs font-medium block mb-1">Tipo:</label>
                          <Select
                            value={msg.type}
                            onValueChange={(value) => updateMessage(resp.id, msg.id, 'type', value)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="text">
                                <div className="flex items-center gap-2">
                                  <Type className="w-4 h-4" />
                                  Texto
                                </div>
                              </SelectItem>
                              <SelectItem value="image">
                                <div className="flex items-center gap-2">
                                  <Image className="w-4 h-4" />
                                  Imagem
                                </div>
                              </SelectItem>
                              <SelectItem value="video">
                                <div className="flex items-center gap-2">
                                  <Video className="w-4 h-4" />
                                  Vídeo
                                </div>
                              </SelectItem>
                              <SelectItem value="audio">
                                <div className="flex items-center gap-2">
                                  <Mic className="w-4 h-4" />
                                  Áudio
                                </div>
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        {/* Delay */}
                        <div>
                          <label className="text-xs font-medium block mb-1 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Delay (segundos):
                          </label>
                          <Input
                            type="number"
                            min="0"
                            max="60"
                            value={msg.delay}
                            onChange={(e) => updateMessage(resp.id, msg.id, 'delay', parseInt(e.target.value))}
                            placeholder="0-60"
                          />
                        </div>
                      </div>
                      
                      {/* Conteúdo */}
                      <div>
                        <label className="text-xs font-medium block mb-1">
                          {msg.type === 'text' ? 'Texto:' : 'URL:'}
                        </label>
                        {msg.type === 'text' ? (
                          <Textarea
                            placeholder="Digite a resposta..."
                            value={msg.content}
                            onChange={(e) => updateMessage(resp.id, msg.id, 'content', e.target.value)}
                            rows={3}
                          />
                        ) : (
                          <Input
                            placeholder={`URL do ${msg.type === 'image' ? 'imagem' : msg.type === 'video' ? 'vídeo' : 'áudio'}`}
                            value={msg.content}
                            onChange={(e) => updateMessage(resp.id, msg.id, 'content', e.target.value)}
                          />
                        )}
                      </div>
                      
                      {idx < resp.messages.length - 1 && (
                        <div className="text-center text-xs text-slate-400 py-1">
                          ⬇️ Aguarda {msg.delay}s e envia próxima
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Ativo */}
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    checked={resp.active}
                    onChange={(e) => updateResponse(resp.id, 'active', e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label className="text-sm font-medium">Ativo</label>
                </div>
              </div>
            ))
          )}
          
          <Button 
            onClick={saveAutoResponses} 
            disabled={loading}
            className="w-full"
            size="lg"
          >
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Salvando...' : 'Salvar Todas as Auto-Respostas'}
          </Button>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
            <p className="font-medium mb-2">💡 Como Funciona:</p>
            <ul className="list-disc list-inside space-y-1 text-slate-700">
              <li>Cliente envia mensagem com gatilho → Sequência de respostas é enviada automaticamente</li>
              <li>Cada mensagem pode ser texto, imagem, vídeo ou áudio</li>
              <li>Delay: tempo de espera (0-60s) antes de enviar próxima mensagem</li>
              <li>Exemplo: Msg1 (texto) → aguarda 3s → Msg2 (vídeo) → aguarda 5s → Msg3 (texto)</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AutoResponder;
