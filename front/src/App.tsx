import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AuthPage from './pages/AuthPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './components/Dashboard';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import OllamaModelManager from './components/OllamaModelManager';
import AgentDetailPage from './pages/AgentDetailPage';
import SimpleChat from './components/SimpleChat';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/test-chat-public" element={<SimpleChat />} />
          <Route path="/" element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="dashboard/agents" element={<OllamaModelManager />} />
            <Route path="dashboard/agents/:id" element={<AgentDetailPage />} />
            <Route path="knowledge" element={<KnowledgeBasePage />} />
            <Route path="test-chat" element={<SimpleChat />} />
            <Route index element={<Navigate to="/dashboard" replace />} />
          </Route>
          <Route path="*" element={<Navigate to="/auth" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
