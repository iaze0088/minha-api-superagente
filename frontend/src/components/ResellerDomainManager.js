import { useState, useEffect } from 'react';
import { Globe, Copy, Check, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';

const ResellerDomainManager = () => {
  const [domainInfo, setDomainInfo] = useState(null);
  const [customDomain, setCustomDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadDomainInfo();
  }, []);

  const loadDomainInfo = async () => {
    try {
      const { data } = await api.get('/reseller/domain-info');
      setDomainInfo(data);
      setCustomDomain(data.custom_domain || '');
    } catch (error) {
      console.error('Erro ao carregar informações de domínio:', error);
      toast.error('Erro ao carregar configurações de domínio');
    }
  };

  const saveCustomDomain = async () => {
    if (!customDomain.trim()) {
      toast.error('Digite um domínio válido');
      return;
    }

    // Validação básica de domínio
    const domainRegex = /^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/i;
    if (!domainRegex.test(customDomain)) {
      toast.error('Formato de domínio inválido. Use: seudominio.com.br');
      return;
    }

    setLoading(true);
    try {
      await api.post('/reseller/update-domain', {
        custom_domain: customDomain
      });
      toast.success('Domínio personalizado salvo! Configure o DNS e aguarde propagação.');
      loadDomainInfo();
    } catch (error) {
      console.error('Erro ao salvar domínio:', error);
      toast.error('Erro ao salvar domínio personalizado');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success('Copiado para área de transferência!');
    setTimeout(() => setCopied(false), 2000);
  };

  if (!domainInfo) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-gray-400" />
          <p className="text-gray-500">Carregando informações...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Gestão de Domínios</h2>
        <p className="text-gray-600">Configure seu domínio personalizado para o sistema</p>
      </div>

      {/* Domínio de Teste */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600" />
            Domínio de Teste
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">URL de Acesso Atual</label>
            <div className="flex items-center gap-2">
              <Input
                value={domainInfo.test_domain || 'N/A'}
                readOnly
                className="flex-1 bg-gray-50"
              />
              <Button
                variant="outline"
                onClick={() => copyToClipboard(domainInfo.test_domain)}
                className="flex items-center gap-2"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                Copiar
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Este é seu domínio temporário para testes. Funciona imediatamente sem configuração.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Domínio Personalizado */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-green-600" />
            Domínio Personalizado
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Seu Domínio (ex: suporte.suaempresa.com.br)
            </label>
            <div className="flex items-center gap-2">
              <Input
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
                placeholder="suporte.suaempresa.com.br"
                className="flex-1"
              />
              <Button
                onClick={saveCustomDomain}
                disabled={loading}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
                Salvar
              </Button>
            </div>
          </div>

          {customDomain && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-bold text-blue-900 mb-2">
                    Configuração DNS Necessária
                  </h4>
                  <p className="text-sm text-blue-800 mb-3">
                    Para que seu domínio funcione, você precisa configurar os seguintes registros DNS:
                  </p>
                  
                  <div className="space-y-3 text-sm">
                    {/* Registro A */}
                    <div className="bg-white rounded p-3 border border-blue-200">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-bold text-blue-900">Tipo A (Obrigatório)</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(domainInfo.server_ip)}
                          className="h-6 px-2"
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-600">Nome:</span>
                          <span className="ml-2 font-mono bg-gray-100 px-2 py-1 rounded">
                            {customDomain.split('.')[0]}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Valor:</span>
                          <span className="ml-2 font-mono bg-gray-100 px-2 py-1 rounded">
                            {domainInfo.server_ip}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Registro CNAME (alternativo) */}
                    <div className="bg-white rounded p-3 border border-blue-200">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-bold text-blue-900">Tipo CNAME (Alternativo)</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(domainInfo.test_domain)}
                          className="h-6 px-2"
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-600">Nome:</span>
                          <span className="ml-2 font-mono bg-gray-100 px-2 py-1 rounded">
                            {customDomain.split('.')[0]}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Valor:</span>
                          <span className="ml-2 font-mono bg-gray-100 px-2 py-1 rounded">
                            {domainInfo.test_domain}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <p className="text-xs text-blue-800">
                      <strong>Tempo de propagação:</strong> 24-48 horas<br/>
                      <strong>Recomendação:</strong> Configure o registro A para melhor performance
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status do Domínio */}
      <Card>
        <CardHeader>
          <CardTitle>Status da Configuração</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium">Domínio de Teste:</span>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-bold">
                ✅ Ativo
              </span>
            </div>
            
            {customDomain && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm font-medium">Domínio Personalizado:</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  domainInfo.custom_domain_verified 
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {domainInfo.custom_domain_verified ? '✅ Verificado' : '⏳ Pendente DNS'}
                </span>
              </div>
            )}
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium">SSL/HTTPS:</span>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-bold">
                ✅ Ativo
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Informações Adicionais */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <CardContent className="p-4">
          <h4 className="font-bold text-purple-900 mb-2 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Dicas Importantes
          </h4>
          <ul className="text-sm text-purple-800 space-y-1 ml-6 list-disc">
            <li>Use sempre o domínio de teste enquanto configura o DNS</li>
            <li>Certificados SSL são gerados automaticamente para domínios verificados</li>
            <li>Após configurar o DNS, aguarde 24-48h para propagação completa</li>
            <li>Você pode usar subdomínios (ex: chat.seudominio.com)</li>
            <li>Entre em contato com suporte se tiver dúvidas na configuração</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResellerDomainManager;
