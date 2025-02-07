import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Pages
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Devices from '../pages/Devices';
import CLI from '../pages/CLI';
import Admin from '../pages/Admin';
import NotFound from '../pages/NotFound';

// Protected Route wrapper
const ProtectedRoute = ({ children, adminOnly = false }: { children: React.ReactNode, adminOnly?: boolean }) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && user?.role !== 'admin') {
    return <Navigate to="/" />;
  }

  return <>{children}</>;
};

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/devices" element={
        <ProtectedRoute>
          <Devices />
        </ProtectedRoute>
      } />
      
      <Route path="/cli" element={
        <ProtectedRoute>
          <CLI />
        </ProtectedRoute>
      } />
      
      <Route path="/admin" element={
        <ProtectedRoute adminOnly>
          <Admin />
        </ProtectedRoute>
      } />

      {/* 404 route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
} 