import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import AdminLogin from './pages/AdminLogin';
import AgentLogin from './pages/AgentLogin';
import ClientLogin from './pages/ClientLogin';
import AdminDashboard from './pages/AdminDashboard';
import AgentDashboard from './pages/AgentDashboard';
import ClientChat from './pages/ClientChat';
import Home from './pages/Home';
import PrivateRoute from './components/PrivateRoute';
import './App.css';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/agent/login" element={<AgentLogin />} />
          <Route path="/client/login" element={<ClientLogin />} />
          
          <Route path="/admin" element={
            <PrivateRoute requiredType="admin">
              <AdminDashboard />
            </PrivateRoute>
          } />
          
          <Route path="/agent" element={
            <PrivateRoute requiredType="agent">
              <AgentDashboard />
            </PrivateRoute>
          } />
          
          <Route path="/client" element={
            <PrivateRoute requiredType="client">
              <ClientChat />
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
