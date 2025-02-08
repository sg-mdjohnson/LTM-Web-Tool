import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import theme from './theme';

import LoginPage from './components/auth/LoginPage';
import MainLayout from './components/layout/MainLayout';
import ProtectedRoute from './components/common/ProtectedRoute';
import DeviceList from './components/devices/DeviceList';
import DNSTools from './components/dns/DNSTools';
import AdminPanel from './components/admin/AdminPanel';

export default function App() {
  return (
    <ChakraProvider theme={theme}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <Routes>
                      <Route path="/" element={<Navigate to="/devices" replace />} />
                      <Route path="/devices" element={<DeviceList />} />
                      <Route path="/dns" element={<DNSTools />} />
                      <Route path="/admin" element={<AdminPanel />} />
                    </Routes>
                  </MainLayout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ChakraProvider>
  );
} 