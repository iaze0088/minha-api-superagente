import axios from 'axios';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

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

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user_type');
      localStorage.removeItem('user_data');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;

// WebSocket connection
export const createWebSocket = (userId) => {
  const wsUrl = API_URL.replace('http', 'ws');
  return new WebSocket(`${wsUrl}/ws/${userId}`);
};
