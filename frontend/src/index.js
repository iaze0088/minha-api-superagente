import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
// import { registerServiceWorker } from './register-sw';

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// SERVICE WORKER COMPLETAMENTE DESABILITADO
// registerServiceWorker();

// Desregistrar TODOS os service workers existentes
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(registrations => {
    for (let registration of registrations) {
      registration.unregister();
      console.log('🗑️ Service Worker removido:', registration.scope);
    }
    console.log('✅ Todos os Service Workers foram removidos');
  });
  
  // Limpar todos os caches do service worker
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => {
        caches.delete(name);
        console.log('🗑️ Cache removido:', name);
      });
    });
  }
}
