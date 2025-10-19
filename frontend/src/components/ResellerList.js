import { Card, Button, Input } from '@/components/ui';
import { Users, Trash2, ArrowRightLeft } from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';

const ResellerList = ({ resellers, loadData, handleDeleteReseller, setTransferModal }) => (
  <div className="grid gap-4">
    {resellers.length === 0 ? (
      <Card className="p-8 text-center">
        <Users className="w-16 h-16 mx-auto text-slate-300 mb-4" />
        <p className="text-slate-600">Nenhuma revenda criada ainda</p>
        <p className="text-sm text-slate-500 mt-2">Crie sua primeira revenda acima</p>
      </Card>
    ) : (
      resellers.map((reseller) => (
        <ResellerCard 
          key={reseller.id}
          reseller={reseller}
          loadData={loadData}
          handleDeleteReseller={handleDeleteReseller}
          setTransferModal={setTransferModal}
        />
      ))
    )}
  </div>
);

const ResellerCard = ({ reseller, loadData, handleDeleteReseller, setTransferModal }) => (
  <Card className="p-6 hover:shadow-lg transition-shadow">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-2xl">{reseller.level === 0 ? '🌟' : reseller.level === 1 ? '📦' : '📁'}</span>
          <div>
            <h4 className="font-semibold text-slate-900 text-lg">{reseller.name}</h4>
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
              Nível {reseller.level || 0} {reseller.parent_id ? '(Sub-revenda)' : '(Raiz)'}
            </span>
          </div>
        </div>
        
        <div className="space-y-1 text-sm text-slate-600">
          <p>✉️ Email: {reseller.email}</p>
          {reseller.domain && <p>🔗 Subdomínio: {reseller.domain}</p>}
          {reseller.custom_domain && (
            <p className="text-emerald-600 font-medium">✅ Domínio: {reseller.custom_domain}</p>
          )}
          {reseller.children_count > 0 && (
            <p className="text-orange-600 font-medium">
              👥 {reseller.children_count} Sub-revenda(s)
            </p>
          )}
          <p className="text-xs text-slate-500">
            📅 Criado: {new Date(reseller.created_at).toLocaleDateString('pt-BR')}
          </p>
        </div>

        <div className="mt-3 flex gap-2">
          <Input
            placeholder="Domínio customizado (ex: ajuda.vip)"
            defaultValue={reseller.custom_domain}
            id={`domain-${reseller.id}`}
            className="text-sm flex-1"
          />
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              const input = document.getElementById(`domain-${reseller.id}`);
              const domain = input.value.trim();
              try {
                await api.put(`/resellers/${reseller.id}`, { custom_domain: domain });
                toast.success('Domínio atualizado!');
                loadData();
              } catch (error) {
                toast.error('Erro ao atualizar domínio');
              }
            }}
          >
            💾 Salvar
          </Button>
        </div>

        <div className="mt-3">
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            reseller.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {reseller.is_active ? '✓ Ativa' : '✗ Inativa'}
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open(`/revenda/login?email=${reseller.email}`, '_blank')}
        >
          🚀 Ver Painel
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setTransferModal({ open: true, reseller, new_parent_id: null })}
        >
          <ArrowRightLeft className="w-4 h-4 mr-1" />
          Transferir
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDeleteReseller(reseller.id)}
          className="text-red-600 hover:bg-red-50"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  </Card>
);

export default ResellerList;
