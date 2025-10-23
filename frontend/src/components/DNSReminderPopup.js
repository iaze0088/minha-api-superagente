import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { AlertTriangle, Clock } from 'lucide-react';

const DNSReminderPopup = ({ resellerData, onClose }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [countdown, setCountdown] = useState(30);
  const [timeRemaining, setTimeRemaining] = useState('');

  useEffect(() => {
    if (!resellerData) return;

    // Verificar se já tem domínio customizado
    if (resellerData.custom_domain) {
      return; // Já configurou, não mostrar pop-up
    }

    // Calcular tempo desde criação
    const createdAt = new Date(resellerData.created_at);
    const now = new Date();
    const hoursSinceCreation = (now - createdAt) / (1000 * 60 * 60);

    // Se passou mais de 24h, não mostrar
    if (hoursSinceCreation > 24) {
      return;
    }

    // Calcular tempo restante
    const hoursRemaining = Math.max(0, 24 - hoursSinceCreation);
    setTimeRemaining(`${Math.floor(hoursRemaining)}h ${Math.floor((hoursRemaining % 1) * 60)}min`);

    // Verificar última exibição do pop-up
    const lastShown = localStorage.getItem(`dns_reminder_${resellerData.id}`);
    const now_time = Date.now();

    if (!lastShown || (now_time - parseInt(lastShown)) > 30 * 60 * 1000) {
      // Mostrar se nunca foi exibido OU se passou mais de 30 minutos
      setIsOpen(true);
      localStorage.setItem(`dns_reminder_${resellerData.id}`, now_time.toString());
    }

    // Agendar próximo pop-up em 30 minutos
    const timer = setTimeout(() => {
      setIsOpen(true);
      localStorage.setItem(`dns_reminder_${resellerData.id}`, Date.now().toString());
    }, 30 * 60 * 1000);

    return () => clearTimeout(timer);
  }, [resellerData]);

  useEffect(() => {
    if (!isOpen) return;

    // Countdown de 30 segundos
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          handleClose();
          return 30;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen]);

  const handleClose = () => {
    setIsOpen(false);
    setCountdown(30);
    if (onClose) onClose();
  };

  if (!isOpen || !resellerData) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-orange-600">
            <AlertTriangle className="w-6 h-6" />
            ⏰ Lembrete: Configure seu Domínio!
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-3 mb-3">
              <Clock className="w-6 h-6 text-orange-600 mt-1 flex-shrink-0" />
              <div>
                <p className="font-bold text-orange-900 text-lg mb-1">
                  Prazo de 24 horas!
                </p>
                <p className="text-sm text-orange-800">
                  Tempo restante: <span className="font-bold">{timeRemaining}</span>
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900 font-semibold mb-2">
              📋 O que você precisa fazer:
            </p>
            <ol className="text-sm text-blue-800 space-y-2 ml-5 list-decimal">
              <li>Comprar um domínio próprio (ex: suaempresa.com.br)</li>
              <li>Ir na aba <span className="font-bold">"Domínio"</span> deste painel</li>
              <li>Adicionar seu domínio e seguir as instruções DNS</li>
              <li>Apontar domínio para o IP: <code className="bg-blue-100 px-2 py-1 rounded font-mono">34.57.15.54</code></li>
              <li><span className="font-bold">Avisar o Master</span> que você configurou o domínio</li>
            </ol>
          </div>

          <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
            <p className="text-sm text-red-900 font-bold text-center">
              ⚠️ Após 24 horas, o acesso ao painel será restrito até configurar o domínio!
            </p>
          </div>

          <div className="flex items-center justify-between pt-2">
            <p className="text-xs text-slate-500">
              Este lembrete aparece a cada 30 minutos
            </p>
            <p className="text-sm font-mono text-slate-600">
              Fecha em: <span className="font-bold text-orange-600">{countdown}s</span>
            </p>
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <Button 
            onClick={handleClose}
            className="bg-orange-600 hover:bg-orange-700"
          >
            OK, Entendi!
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DNSReminderPopup;
