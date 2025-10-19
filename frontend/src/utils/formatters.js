// Formatar WhatsApp no formato +55 44 98829-4033
export const formatWhatsApp = (phone) => {
  if (!phone) return '';
  
  // Remove tudo que não é número
  const numbers = phone.replace(/\D/g, '');
  
  // Formato: +55 44 98829-4033
  if (numbers.length === 13) {
    return `+${numbers.slice(0, 2)} ${numbers.slice(2, 4)} ${numbers.slice(4, 9)}-${numbers.slice(9)}`;
  }
  
  // Formato: +55 44 8829-4033 (sem 9 extra)
  if (numbers.length === 12) {
    return `+${numbers.slice(0, 2)} ${numbers.slice(2, 4)} ${numbers.slice(4, 8)}-${numbers.slice(8)}`;
  }
  
  return phone;
};

// Verificar se está em horário de atendimento (9h-23h)
export const isWithinBusinessHours = () => {
  const now = new Date();
  const hours = now.getHours();
  return hours >= 9 && hours < 23;
};

// Verificar se já mostrou pop-up hoje
export const shouldShowQueuePopup = () => {
  const lastShown = localStorage.getItem('last_queue_popup');
  if (!lastShown) return true;
  
  const lastDate = new Date(parseInt(lastShown));
  const today = new Date();
  
  return lastDate.toDateString() !== today.toDateString();
};

export const markQueuePopupShown = () => {
  localStorage.setItem('last_queue_popup', Date.now().toString());
};
