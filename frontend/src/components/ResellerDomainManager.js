import { useState, useEffect } from 'react';
import { Globe, AlertCircle, CheckCircle2, ExternalLink, Copy, Server, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';

const ResellerDomainManager = () => {
  const [domainInfo, setDomainInfo] = useState(null);
  const [newDomain, setNewDomain] = useState('');
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [activating, setActivating] = useState(false);

  useEffect(() => {
    loadDomainInfo();
  }, []);

  const loadDomainInfo = async () => {
    try {
      const { data } = await api.get('/reseller/domain-info');
      setDomainInfo(data);
    } catch (error) {
      console.error('Erro ao carregar info de domínio:', error);
      toast.error('Erro ao carregar informações de domínio');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyDNS = async () => {
    if (!newDomain.trim()) {
      toast.error('Digite um domínio para verificar');
      return;
    }

    setVerifying(true);
    try {
      const { data } = await api.get(`/reseller/verify-domain?domain=${newDomain}`);
      
      if (data.dns_ok) {
        toast.success('✅ DNS configurado corretamente! Pronto para ativar.');
      } else {
        toast.error('❌ DNS não está configurado corretamente. Verifique as instruções.');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao verificar DNS');
    } finally {
      setVerifying(false);
    }
  };

  const handleActivateDomain = async () => {
    if (!newDomain.trim()) {
      toast.error('Digite um domínio para ativar');
      return;
    }

    if (!window.confirm(
      `⚠️ ATENÇÃO:\n\n` +
      `Ao ativar o domínio "${newDomain}", o domínio de teste será DESATIVADO.\n\n` +
      `Você só poderá acessar pelo novo domínio após a ativação.\n\n` +
      `Confirma a ativação?`
    )) {
      return;
    }

    setActivating(true);
    try {
      const { data } = await api.post('/reseller/update-domain', {
        custom_domain: newDomain
      });
      
      if (data.ok) {
        toast.success('✅ Domínio oficial ativado! Acesse pelo novo domínio.', { duration: 7000 });
        setNewDomain('');
        loadDomainInfo();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao ativar domínio');
    } finally {
      setActivating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('✅ Copiado!');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-slate-600">Carregando...</p>
        </div>
      </div>
    );
  }

  const serverIp = '34.57.15.54';

  return (
    <div className="space-y-6">
      {/* Domínio de Teste Atual */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-600" />
          Domínio Provisório (Teste)
        </h3>
        
        <div className="bg-amber-50 border-2 border-amber-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-amber-900 mb-2">
                Este é seu domínio temporário para testes:
              </p>
              <div className="bg-white rounded-lg p-3 border border-amber-300 flex items-center justify-between">
                <code className="text-sm text-amber-900 break-all">{domainInfo?.test_domain || 'N/A'}</code>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={() => copyToClipboard(domainInfo?.test_domain || '')}
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-amber-700 mt-2">
                ⚠️ Este domínio será desativado quando você ativar seu domínio oficial.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Domínio Oficial Atual */}
      {domainInfo?.custom_domain && (
        <Card className="p-6">
          <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            Domínio Oficial Ativo
          </h3>
          
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-green-600" />
                <div>
                  <code className="text-sm font-semibold text-green-900">{domainInfo.custom_domain}</code>
                  <p className="text-xs text-green-700 mt-1">🔒 Domínio Ativo</p>
                </div>
              </div>
              <a 
                href={`https://${domainInfo.custom_domain}/admin`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-600 hover:text-green-800"
              >
                <ExternalLink className="w-5 h-5" />
              </a>
            </div>
          </div>
        </Card>
      )}

      {/* Configurar Novo Domínio */}
      {!domainInfo?.custom_domain && (
        <Card className="p-6">
          <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-purple-600" />
            Configurar Domínio Oficial
          </h3>
          
          <div className="space-y-6">
            {/* Campo de Domínio */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Digite seu domínio próprio:
              </label>
              <div className="flex gap-2">
                <Input
                  placeholder="exemplo.com.br"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value.toLowerCase().trim())}
                  className="flex-1"
                />
                <Button 
                  onClick={handleVerifyDNS}
                  disabled={verifying || !newDomain}
                  variant="outline"
                >
                  {verifying ? 'Verificando...' : 'Verificar DNS'}
                </Button>
              </div>
            </div>

            {/* Instruções DNS */}
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
              <h4 className="font-bold text-blue-900 mb-4 flex items-center gap-2">
                <Server className="w-5 h-5" />
                Instruções de Configuração DNS
              </h4>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-semibold text-blue-900 mb-2">
                    1️⃣ Acesse o painel do seu provedor de domínio
                  </p>
                  <p className="text-xs text-blue-700">
                    (Registro.br, GoDaddy, Hostinger, etc.)
                  </p>
                </div>

                <div>
                  <p className="text-sm font-semibold text-blue-900 mb-2">
                    2️⃣ Adicione um Registro A:
                  </p>
                  <div className="bg-white rounded-lg p-3 border border-blue-300 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-700">Tipo:</span>
                      <code className="text-xs font-mono bg-blue-100 px-2 py-1 rounded">A</code>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-700">Nome/Host:</span>
                      <code className="text-xs font-mono bg-blue-100 px-2 py-1 rounded">@</code>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-700">Valor/IP:</span>
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-mono bg-blue-100 px-2 py-1 rounded font-bold">{serverIp}</code>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => copyToClipboard(serverIp)}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold text-blue-900 mb-2">
                    3️⃣ Adicione um Registro CNAME para "www":
                  </p>
                  <div className="bg-white rounded-lg p-3 border border-blue-300 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-700">Tipo:</span>
                      <code className="text-xs font-mono bg-blue-100 px-2 py-1 rounded">CNAME</code>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-700">Nome/Host:</span>
                      <code className="text-xs font-mono bg-blue-100 px-2 py-1 rounded">www</code>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-700">Valor:</span>
                      <code className="text-xs font-mono bg-blue-100 px-2 py-1 rounded">@</code>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-3">
                  <p className="text-xs text-yellow-800">
                    ⏱️ <strong>Atenção:</strong> As alterações de DNS podem levar de 15 minutos a 48 horas para propagar completamente.
                  </p>
                </div>
              </div>
            </div>

            {/* Botão Ativar */}
            <div className="flex justify-end pt-4">
              <Button
                onClick={handleActivateDomain}
                disabled={activating || !newDomain}
                className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
              >
                {activating ? 'Ativando...' : 'Ativar Domínio Oficial'}
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ResellerDomainManager;
