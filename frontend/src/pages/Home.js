import { useNavigate } from 'react-router-dom';
import { MessageCircle, Shield, Headphones } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="max-w-6xl w-full space-y-12 animate-slide-up">
        <div className="text-center space-y-4">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-3xl flex items-center justify-center shadow-lg">
              <MessageCircle className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold text-slate-900" style={{fontFamily: 'Space Grotesk, sans-serif'}}>
            Sistema de Suporte
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Chat ao vivo profissional com recursos avançados de atendimento
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <Card 
            data-testid="client-access-card"
            className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer group border-2 hover:border-blue-500 bg-white"
            onClick={() => navigate('/client/login')}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <MessageCircle className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900">Cliente</h3>
              <p className="text-slate-600">
                Acesse o chat e converse com nossa equipe de suporte
              </p>
              <Button data-testid="client-login-btn" className="w-full bg-blue-600 hover:bg-blue-700">
                Acessar Chat
              </Button>
            </div>
          </Card>

          <Card 
            data-testid="agent-access-card"
            className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer group border-2 hover:border-indigo-500 bg-white"
            onClick={() => navigate('/agent/login')}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <Headphones className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900">Atendente</h3>
              <p className="text-slate-600">
                Painel de atendimento para gerenciar conversas e tickets
              </p>
              <Button data-testid="agent-login-btn" className="w-full bg-indigo-600 hover:bg-indigo-700">
                Entrar como Atendente
              </Button>
            </div>
          </Card>

          <Card 
            data-testid="admin-access-card"
            className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer group border-2 hover:border-purple-500 bg-white"
            onClick={() => navigate('/admin/login')}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <Shield className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900">Admin</h3>
              <p className="text-slate-600">
                Configurações, atendentes e gerenciamento completo
              </p>
              <Button data-testid="admin-login-btn" className="w-full bg-purple-600 hover:bg-purple-700">
                Entrar como Admin
              </Button>
            </div>
          </Card>
        </div>

        <div className="text-center">
          <p className="text-sm text-slate-500">
            Sistema de chat profissional • Real-time WebSocket • MongoDB
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
