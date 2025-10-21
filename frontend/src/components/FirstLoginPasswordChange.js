import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import api from '../lib/api';
import { toast } from 'sonner';
import { AlertTriangle } from 'lucide-react';

const FirstLoginPasswordChange = ({ isOpen, onSuccess }) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (newPassword.length < 6) {
      toast.error('Senha deve ter no mínimo 6 caracteres');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      toast.error('As senhas não conferem');
      return;
    }
    
    try {
      setLoading(true);
      await api.post('/resellers/change-password', {
        new_password: newPassword
      });
      
      toast.success('Senha alterada com sucesso!');
      onSuccess();
    } catch (error) {
      toast.error('Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-orange-600">
            <AlertTriangle className="w-6 h-6" />
            Troca de Senha Obrigatória
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-sm">
            <p className="font-medium mb-2">🔒 Primeiro Acesso</p>
            <p className="text-slate-700">
              Por segurança, você precisa alterar a senha padrão <code className="bg-orange-100 px-2 py-1 rounded">admin123</code> antes de continuar.
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nova Senha:</label>
              <Input
                type="password"
                placeholder="Mínimo 6 caracteres"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                autoFocus
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Confirmar Nova Senha:</label>
              <Input
                type="password"
                placeholder="Digite novamente"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
            
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Alterando...' : 'Alterar Senha e Continuar'}
            </Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FirstLoginPasswordChange;
