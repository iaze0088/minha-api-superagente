import { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

const InstallPWA = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstall, setShowInstall] = useState(false);

  useEffect(() => {
    // Verifica se já está instalado
    const isInstalled = window.matchMedia('(display-mode: standalone)').matches || 
                       window.navigator.standalone === true;
    
    if (isInstalled) {
      return; // Não mostra se já instalado
    }

    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Mostrar a cada 5 minutos se não instalado
    const interval = setInterval(() => {
      if (!isInstalled && deferredPrompt) {
        setShowInstall(true);
      }
    }, 5 * 60 * 1000);

    // Mostrar ao carregar página se não instalado
    const initialTimer = setTimeout(() => {
      const dismissed = localStorage.getItem('pwa_last_shown');
      const fiveMinAgo = Date.now() - 5 * 60 * 1000;
      
      if (!dismissed || parseInt(dismissed) < fiveMinAgo) {
        setShowInstall(true);
      }
    }, 3000);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      clearInterval(interval);
      clearTimeout(initialTimer);
    };
  }, [deferredPrompt]);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      localStorage.setItem('pwa_installed', 'true');
    }
    
    setDeferredPrompt(null);
    setShowInstall(false);
    localStorage.setItem('pwa_last_shown', Date.now());
  };

  const handleDismiss = () => {
    setShowInstall(false);
    localStorage.setItem('pwa_last_shown', Date.now());
  };

  if (!showInstall) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-slide-up">
      <div className="bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl shadow-2xl p-4 text-white">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <Download className="w-6 h-6 text-white" />
          </div>
          
          <div className="flex-1">
            <h3 className="font-bold mb-1">
              Instalar WA Suporte
            </h3>
            <p className="text-sm text-white/90 mb-3">
              Acesso rápido e funciona offline!
            </p>
            
            <div className="flex gap-2">
              <Button
                onClick={handleInstall}
                className="flex-1 bg-white text-green-600 hover:bg-white/90"
                size="sm"
              >
                Instalar Agora
              </Button>
              <Button
                onClick={handleDismiss}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20"
              >
                Depois
              </Button>
            </div>
          </div>
          
          <button
            onClick={handleDismiss}
            className="text-white/70 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default InstallPWA;
