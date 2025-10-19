import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, Mail, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../lib/api';
import { setAuth } from '../lib/auth';

const ResellerLogin = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { data } = await api.post('/resellers/login', { email, password });
      setAuth(data.token, data.user_type, data.user_data);
      toast.success(`Bem-vindo, ${data.user_data.name}!`);
      navigate('/revenda/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Email ou senha inválidos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 space-y-6 bg-white shadow-2xl">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 bg-emerald-600 rounded-2xl flex items-center justify-center">
            <Store className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Painel de Revenda
          </h2>
          <p className="text-slate-600 text-center">
            Faça login para gerenciar sua revenda
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="reseller-email-input"
                type="email"
                placeholder="seu-email@exemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                data-testid="reseller-password-input"
                type="password"
                placeholder="Sua senha"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <Button 
            data-testid="reseller-submit-btn"
            type="submit" 
            className="w-full bg-emerald-600 hover:bg-emerald-700" 
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default ResellerLogin;
