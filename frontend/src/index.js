import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { registerServiceWorker } from './register-sw';

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Registrar Service Worker APENAS em produção
if (process.env.NODE_ENV === 'production') {
  registerServiceWorker();
} else {
  console.log('🔧 Service Worker DESABILITADO em desenvolvimento para permitir hot reload');
  
  // Desregistrar service workers existentes em desenvolvimento
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(registrations => {
      for (let registration of registrations) {
        registration.unregister();
        console.log('🗑️ Service Worker desregistrado');
      }
    });
  }
}
