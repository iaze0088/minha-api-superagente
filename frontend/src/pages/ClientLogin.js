import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Phone, Hash } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';
import { setAuth } from '../lib/auth';

const ClientLogin = () => {
  const navigate = useNavigate();
  const [whatsapp, setWhatsapp] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { data } = await api.post('/auth/client/login', { whatsapp, pin });
      setAuth(data.token, data.user_type, data.user_data);
      toast.success('Bem-vindo ao chat!');
      navigate('/client');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-teal-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center">
            <MessageCircle className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Área do Cliente
          </h2>
          <p className="text-slate-600 text-center">
            Entre com seu WhatsApp e PIN para acessar o chat
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">WhatsApp</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="client-whatsapp-input"
                type="text"
                placeholder="55 11 99999-9999"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                className="pl-10"
                required
              />
            </div>
            <p className="text-xs text-slate-500">
              Formato: código do país + DDD + número
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">PIN (2 dígitos)</label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="client-pin-input"
                type="password"
                placeholder="00"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 2))}
                className="pl-10"
                maxLength={2}
                required
              />
            </div>
            <p className="text-xs text-slate-500">
              Primeiro acesso? Crie seu PIN de 2 dígitos
            </p>
          </div>

          <Button 
            data-testid="client-submit-btn"
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700" 
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Avançar'}
          </Button>
        </form>

        <Button
          data-testid="back-home-btn"
          variant="outline"
          onClick={() => navigate('/')}
          className="w-full"
        >
          Voltar
        </Button>
      </Card>
    </div>
  );
};

export default ClientLogin;
