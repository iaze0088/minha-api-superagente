import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, Clock, Users } from 'lucide-react';

const AlertModal = ({ isOpen, onClose, title, message, icon = 'info', autoCloseDelay = 30000 }) => {
  useEffect(() => {
    if (isOpen && autoCloseDelay > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, autoCloseDelay);
      
      return () => clearTimeout(timer);
    }
  }, [isOpen, autoCloseDelay, onClose]);

  if (!isOpen) return null;

  const getIcon = () => {
    switch (icon) {
      case 'warning':
        return <AlertCircle className="w-16 h-16 text-orange-500" />;
      case 'clock':
        return <Clock className="w-16 h-16 text-blue-500" />;
      case 'queue':
        return <Users className="w-16 h-16 text-indigo-500" />;
      default:
        return <AlertCircle className="w-16 h-16 text-blue-500" />;
    }
  };

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8 animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col items-center text-center space-y-4">
          {getIcon()}
          
          <h3 className="text-2xl font-bold text-slate-900">
            {title}
          </h3>
          
          <p className="text-slate-600 text-base leading-relaxed">
            {message}
          </p>
          
          <Button
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 text-lg font-semibold"
            data-testid="alert-modal-ok-btn"
          >
            OK
          </Button>
          
          <p className="text-xs text-slate-400">
            Fecha automaticamente em {autoCloseDelay / 1000}s
          </p>
        </div>
      </div>
    </div>
  );
};

export default AlertModal;
