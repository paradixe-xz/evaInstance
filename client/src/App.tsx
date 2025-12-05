import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { AgentesPage } from './pages/AgentesPage';
import { CreateAgentPage } from './pages/agent/CreateAgentPage';
import { AgentDetailPage } from './pages/agent/AgentDetailPage';
import { WhatsAppPage } from './pages/whatsapp/WhatsAppPage';

// Create a client
const queryClient = new QueryClient();

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) {
    // Redirigir a login, guardando la ubicación actual para redirigir después del login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Si el usuario está autenticado, redirigir al dashboard
  if (user) {
    const from = (location.state as any)?.from?.pathname || '/dashboard';
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route path="/dashboard" element={
        <PrivateRoute>
          <DashboardPage />
        </PrivateRoute>
      } />
      <Route
        path="/dashboard/agentes"
        element={
          <PrivateRoute>
            <AgentesPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/dashboard/whatsapp"
        element={
          <PrivateRoute>
            <WhatsAppPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/dashboard/agentes/nuevo"
        element={
          <PrivateRoute>
            <CreateAgentPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/dashboard/agentes/:id"
        element={
          <PrivateRoute>
            <AgentDetailPage />
          </PrivateRoute>
        }
      >
        <Route index element={<AgentDetailPage />} />
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <AppRoutes />
            <Toaster position="top-center" richColors />
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </div>
  );
}

export default App;
