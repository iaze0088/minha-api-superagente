import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Toaster } from '@/components/ui/sonner';
import AdminLogin from './pages/AdminLogin';
import AgentLogin from './pages/AgentLogin';
import ClientLogin from './pages/ClientLogin';
import ResellerLogin from './pages/ResellerLogin';
import AdminDashboard from './pages/AdminDashboard';
import AgentDashboard from './pages/AgentDashboard';
import ResellerDashboard from './pages/ResellerDashboard';
import ClientChat from './pages/ClientChat';
import Home from './pages/Home';
import PrivateRoute from './components/PrivateRoute';
import './App.css';

function App() {
  useEffect(() => {
    // Força reload uma única vez após limpar cache
    const cacheCleared = localStorage.getItem('cache_cleared_v2');
    if (!cacheCleared) {
      console.log('🔄 Limpando cache e recarregando...');
      localStorage.setItem('cache_cleared_v2', 'true');
      window.location.reload(true);
    }
  }, []);
  
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Cliente é a home */}
          <Route path="/" element={<ClientLogin />} />
          <Route path="/chat" element={
            <PrivateRoute requiredType="client">
              <ClientChat />
            </PrivateRoute>
          } />
          
          {/* Atendente */}
          <Route path="/atendente/login" element={<AgentLogin />} />
          <Route path="/atendente" element={
            <PrivateRoute requiredType="agent">
              <AgentDashboard />
            </PrivateRoute>
          } />
          
          {/* Admin */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={
            <PrivateRoute requiredType="admin">
              <AdminDashboard />
            </PrivateRoute>
          } />
          
          {/* Revenda */}
          <Route path="/revenda/login" element={<ResellerLogin />} />
          <Route path="/revenda/dashboard" element={
            <PrivateRoute requiredType="reseller">
              <ResellerDashboard />
            </PrivateRoute>
          } />
          
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
