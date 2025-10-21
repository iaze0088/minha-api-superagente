import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_URL = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors - NÃO FORÇAR LOGOUT NUNCA
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Apenas rejeitar o erro sem desconectar o usuário
    // Sessão persiste indefinidamente até logout manual
    console.log('API Error:', error.response?.status, error.config?.url);
    return Promise.reject(error);
  }
);

export default api;

// WebSocket connection
export const createWebSocket = (userId) => {
  const wsUrl = API_URL.replace('http', 'ws');
  // Gera session ID único
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = Date.now().toString() + Math.random().toString(36);
    localStorage.setItem('session_id', sessionId);
  }
  return new WebSocket(`${wsUrl}/ws/${userId}/${sessionId}`);
};
