import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import theme from './theme';
import ErrorBoundary from './components/common/ErrorBoundary';

import LoginPage from './components/auth/LoginPage';
import MainLayout from './components/layout/MainLayout';
import ProtectedRoute from './components/common/ProtectedRoute';
import DeviceList from './components/devices/DeviceList';
import DNSTools from './components/dns/DNSTools';
import AdminPanel from './components/admin/AdminPanel';

export default function App() {
  console.log('App rendering...');
  return (
    <ChakraProvider theme={theme}>
      <ErrorBoundary>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <ErrorBoundary>
                        <Routes>
                          <Route path="/" element={<Navigate to="/devices" replace />} />
                          <Route path="/devices" element={<DeviceList />} />
                          <Route path="/dns" element={<DNSTools />} />
                          <Route path="/admin" element={<AdminPanel />} />
                        </Routes>
                      </ErrorBoundary>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ErrorBoundary>
    </ChakraProvider>
  );
} 