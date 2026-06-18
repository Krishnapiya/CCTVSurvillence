import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import ROIManagement from './pages/ROIManagement'
import ROIListPage from './pages/ROIListPage'
import CameraManagement from './pages/CameraManagement'
import EventLogs from './pages/EventLogs'
import SettingsPage from './pages/SettingsPage'
import EventAlertJobs from './pages/EventAlertJobs'
import MainLayout from './components/Layout/MainLayout'

// Simple Auth Guard Component
const ProtectedRoute = () => {
  const isAuthenticated = localStorage.getItem('surv_auth') === 'true';
  const token = localStorage.getItem('surv_token');
  
  if (!isAuthenticated || !token) {
    localStorage.removeItem('surv_auth');
    localStorage.removeItem('surv_token');
    return <Navigate to="/login" replace />;
  }
  
  return <Outlet />;
};

function App() {
  return (
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected Routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Navigate to="/" replace />} />
          <Route path="roi" element={<ROIManagement />} />
          <Route path="rois" element={<ROIListPage />} />
          <Route path="cameras" element={<CameraManagement />} />
          <Route path="event-jobs" element={<EventAlertJobs />} />
          <Route path="logs" element={<EventLogs />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>

      {/* Catch-all Redirect */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
