// Som de notificação
export const playNotificationSound = () => {
  try {
    const audio = new Audio('/notification.mp3');
    audio.volume = 0.5;
    audio.play().catch(err => console.log('Audio play failed:', err));
  } catch (error) {
    console.log('Notification sound error:', error);
  }
};

// Vibração
export const vibrate = () => {
  if ('vibrate' in navigator) {
    navigator.vibrate([200, 100, 200]);
  }
};

// Notificação push (se PWA instalado)
export const showPushNotification = (title, body) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, {
      body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      vibrate: [200, 100, 200],
      tag: 'chat-message'
    });
  }
};

// Pedir permissão de notificação
export const requestNotificationPermission = async () => {
  if ('Notification' in window && Notification.permission === 'default') {
    await Notification.requestPermission();
  }
};
