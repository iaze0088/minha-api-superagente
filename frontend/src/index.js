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

// SERVICE WORKER DESABILITADO TEMPORARIAMENTE PARA DEBUG
// registerServiceWorker();

// Desregistrar service workers existentes
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(registrations => {
    for (let registration of registrations) {
      registration.unregister();
      console.log('🔴 Service Worker desregistrado');
    }
  });
}
